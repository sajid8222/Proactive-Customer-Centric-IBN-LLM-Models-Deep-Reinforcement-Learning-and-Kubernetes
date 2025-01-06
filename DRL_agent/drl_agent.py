# # drl_agent/drl_agent.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from stable_baselines3 import SAC
from flask import Flask
from kubernetes import client, config
import time
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Load Kubernetes configuration
config.load_incluster_config()
api_client = client.ApiClient()

class SAGINEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(SAGINEnv, self).__init__()
        try:
            # Try loading in-cluster config
            config.load_incluster_config()
        except:
            # Fallback to local kubeconfig
            config.load_kube_config()

        self.num_customers = 1  # Assuming one customer for simplicity

        self.action_space = spaces.Box(low=-1, high=1, shape=(self.num_customers * 3,), dtype=np.float32)

        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(self.num_customers * 3 + 2,), dtype=np.float32)

        self.state = None

        # Default maximums (will be updated based on quotas)
        self.max_cpu_per_customer = 8
        self.max_mem_per_customer = 16
        self.max_replicas_per_customer = 5

        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.metrics_api = client.CustomObjectsApi()
        self.api = client.ApiClient()

        # Get resource quotas
        self.update_resource_limits()

    def update_resource_limits(self):
        for i in range(self.num_customers):
            customer_namespace = f"customer-{chr(ord('a') + i)}"
            cpu_limit, mem_limit = self.get_resource_quota(customer_namespace)
            if cpu_limit:
                self.max_cpu_per_customer = cpu_limit
            if mem_limit:
                self.max_mem_per_customer = mem_limit

    def get_resource_quota(self, namespace):
        try:
            quotas = self.v1.list_namespaced_resource_quota(namespace=namespace).items
            for quota in quotas:
                cpu_limit = quota.status.hard.get('limits.cpu')
                mem_limit = quota.status.hard.get('limits.memory')
                cpu_limit = self.parse_cpu(cpu_limit) if cpu_limit else None
                mem_limit = self.parse_memory(mem_limit) if mem_limit else None
                return cpu_limit, mem_limit
        except client.exceptions.ApiException as e:
            print(f"Error getting resource quotas: {e}")
        return None, None

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.state = self.get_state()
        return self.state, {}

    def step(self, action):
        action = np.clip(action, self.action_space.low, self.action_space.high)

        for i in range(self.num_customers):
            delta_cpu = action[i * 3]
            delta_mem = action[i * 3 + 1]
            delta_rep = action[i * 3 + 2]

            customer_namespace = f"customer-{chr(ord('a') + i)}"

            self.adjust_resources(customer_namespace, delta_cpu, delta_mem)
            self.adjust_replicas(customer_namespace, delta_rep)

        self.state = self.get_state()
        reward = self.compute_reward()
        terminated = False
        truncated = False
        info = {}

        return self.state, reward, terminated, truncated, info

    def render(self, mode='human'):
        pass

    def close(self):
        pass

    def adjust_resources(self, namespace, delta_cpu, delta_mem):
        deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace).items

        # Get current resource quotas
        cpu_quota, mem_quota = self.get_resource_quota(namespace)

        for deployment in deployments:
            containers = deployment.spec.template.spec.containers
            container_patches = []
            for container in containers:
                current_cpu = self.parse_cpu(container.resources.requests.get('cpu', '0'))
                new_cpu = current_cpu + delta_cpu * self.max_cpu_per_customer
                new_cpu = np.clip(new_cpu, 0.1, cpu_quota or self.max_cpu_per_customer)

                current_mem = self.parse_memory(container.resources.requests.get('memory', '0'))
                new_mem = current_mem + delta_mem * self.max_mem_per_customer
                new_mem = np.clip(new_mem, 0.1, mem_quota or self.max_mem_per_customer)

                container_patch = {
                    'name': container.name,
                    'resources': {
                        'requests': {
                            'cpu': f"{new_cpu}",
                            'memory': f"{new_mem}Gi"
                        },
                        'limits': {
                            'cpu': f"{new_cpu}",
                            'memory': f"{new_mem}Gi"
                        }
                    }
                }
                container_patches.append(container_patch)

            patch_body = {
                'spec': {
                    'template': {
                        'spec': {
                            'containers': container_patches
                        }
                    }
                }
            }

            try:
                self.apps_v1.patch_namespaced_deployment(
                    name=deployment.metadata.name,
                    namespace=namespace,
                    body=patch_body
                )
            except client.exceptions.ApiException as e:
                print(f"Error adjusting resources for {deployment.metadata.name}: {e}")

    def adjust_replicas(self, namespace, delta_rep):
        deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace).items

        for deployment in deployments:
            current_replicas = deployment.spec.replicas or 1
            delta_replicas = int(np.round(delta_rep * self.max_replicas_per_customer))
            new_replicas = int(np.clip(current_replicas + delta_replicas, 1, self.max_replicas_per_customer))

            patch_body = {
                'spec': {
                    'replicas': new_replicas
                }
            }

            try:
                self.apps_v1.patch_namespaced_deployment(
                    name=deployment.metadata.name,
                    namespace=namespace,
                    body=patch_body
                )
            except client.exceptions.ApiException as e:
                print(f"Error adjusting replicas for {deployment.metadata.name}: {e}")

    def get_state(self):
        state = []

        total_cpu_usage = 0
        total_cpu_capacity = 0
        total_mem_usage = 0
        total_mem_capacity = 0

        for i in range(self.num_customers):
            customer_namespace = f"customer-{chr(ord('a') + i)}"
            pods = self.v1.list_namespaced_pod(namespace=customer_namespace).items

            cpu_usage = 0
            cpu_allocated = 0
            mem_usage = 0
            mem_allocated = 0
            num_replicas = 0

            try:
                pod_metrics = self.metrics_api.list_namespaced_custom_object(
                    group="metrics.k8s.io",
                    version="v1beta1",
                    namespace=customer_namespace,
                    plural="pods"
                )
            except client.exceptions.ApiException as e:
                print(f"Error getting pod metrics: {e}")
                pod_metrics = {'items': []}

            metrics_mapping = {item['metadata']['name']: item for item in pod_metrics.get('items', [])}

            for pod in pods:
                pod_name = pod.metadata.name
                pod_metric = metrics_mapping.get(pod_name)
                if pod_metric:
                    for container in pod_metric['containers']:
                        cpu_usage += self.parse_cpu_usage(container['usage']['cpu'])
                        mem_usage += self.parse_memory_usage(container['usage']['memory'])

                for container in pod.spec.containers:
                    cpu_allocated += self.parse_cpu(container.resources.requests.get('cpu', '0'))
                    mem_allocated += self.parse_memory(container.resources.requests.get('memory', '0'))

                num_replicas += 1

            cpu_usage_normalized = cpu_usage / (cpu_allocated + 1e-5)
            mem_usage_normalized = mem_usage / (mem_allocated + 1e-5)
            replicas_normalized = num_replicas / self.max_replicas_per_customer

            state.extend([cpu_usage_normalized, mem_usage_normalized, replicas_normalized])

            total_cpu_usage += cpu_usage
            total_cpu_capacity += self.max_cpu_per_customer
            total_mem_usage += mem_usage
            total_mem_capacity += self.max_mem_per_customer

        cluster_cpu_utilization = total_cpu_usage / (total_cpu_capacity + 1e-5)
        cluster_mem_utilization = total_mem_usage / (total_mem_capacity + 1e-5)

        state.extend([cluster_cpu_utilization, cluster_mem_utilization])

        return np.array(state, dtype=np.float32)

    def compute_reward(self):
        state = self.state
        total_penalty = 0

        for i in range(self.num_customers):
            cpu_usage = state[i * 3]
            mem_usage = state[i * 3 + 1]

            optimal_utilization = 0.8
            cpu_penalty = (cpu_usage - optimal_utilization) ** 2
            mem_penalty = (mem_usage - optimal_utilization) ** 2

            total_penalty += cpu_penalty + mem_penalty

        cluster_cpu_utilization = state[-2]
        cluster_mem_utilization = state[-1]
        cluster_penalty = max(0, cluster_cpu_utilization - 1) ** 2 + max(0, cluster_mem_utilization - 1) ** 2

        reward = - (total_penalty + cluster_penalty)

        return reward

    def parse_cpu(self, cpu_str):
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        else:
            try:
                return float(cpu_str)
            except:
                return 0

    def parse_memory(self, mem_str):
        if mem_str.endswith('Gi'):
            return float(mem_str[:-2])
        elif mem_str.endswith('Mi'):
            return float(mem_str[:-2]) / 1024
        elif mem_str.endswith('Ki'):
            return float(mem_str[:-2]) / (1024 ** 2)
        elif mem_str.endswith('m'):
            # Convert millibytes to GB
            return float(mem_str[:-1]) / (1024 ** 3 * 1000)
        else:
            try:
                return float(mem_str) / (1024 ** 3)
            except:
                return 0

    def parse_cpu_usage(self, cpu_str):
        if cpu_str.endswith('n'):
            return float(cpu_str[:-1]) / 1e9
        elif cpu_str.endswith('u'):
            return float(cpu_str[:-1]) / 1e6
        elif cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1e3
        else:
            try:
                return float(cpu_str)
            except:
                return 0

    def parse_memory_usage(self, mem_str):
        if mem_str.endswith('Gi'):
            return float(mem_str[:-2])
        elif mem_str.endswith('Mi'):
            return float(mem_str[:-2]) / 1024
        elif mem_str.endswith('Ki'):
            return float(mem_str[:-2]) / (1024 ** 2)
        else:
            try:
                return float(mem_str) / (1024 ** 3)
            except:
                return 0

    def monitor_and_adjust():
        while True:
            try:
                # Monitor resource usage
                v1 = client.CoreV1Api()
                metrics = v1.read_namespaced_pod(name="xr-application-0", namespace="network-hub")
                # Placeholder for actual resource usage
                # For example, CPU and memory usage can be fetched using metrics-server or Prometheus

                # Simulate resource usage (for demonstration)
                import random
                cpu_usage = random.uniform(0, 100)
                memory_usage = random.uniform(0, 100)
                logging.info(f"CPU Usage: {cpu_usage}%, Memory Usage: {memory_usage}%")

                # Adjust resources based on usage
                if cpu_usage > 80 or memory_usage > 80:
                    # Increase replicas
                    scale_deployment(replicas=2)
                else:
                    # Decrease replicas
                    scale_deployment(replicas=1)

                time.sleep(60)  # Wait for 1 minute before next check
            except Exception as e:
                logging.error("Error in DRL Agent", exc_info=True)
                time.sleep(60)

    def scale_deployment(replicas):
        apps_v1 = client.AppsV1Api()
        deployment = apps_v1.read_namespaced_deployment(name="xr-application", namespace="network-hub")
        deployment.spec.replicas = replicas
        apps_v1.patch_namespaced_deployment(name="xr-application", namespace="network-hub", body=deployment)
        logging.info(f"Scaled xr-application to {replicas} replicas")

if __name__ == "__main__":
    monitor_and_adjust()
    env = SAGINEnv()
    model = SAC('MlpPolicy', env, verbose=1)
    model.learn(total_timesteps=10000)
