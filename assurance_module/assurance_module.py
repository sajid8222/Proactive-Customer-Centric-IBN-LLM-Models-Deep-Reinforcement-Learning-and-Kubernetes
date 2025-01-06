#assurance_module.py
from flask import Flask, jsonify
from kubernetes import client, config
import time
import logging
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Load Kubernetes configuration
config.load_incluster_config()
api_client = client.ApiClient()

GUI_URL = "http://gui-service:5000/notify_operator"

def monitor_usage():
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

            # Notify operator if usage exceeds threshold
            if cpu_usage > 80 or memory_usage > 80:
                notify_operator(cpu_usage, memory_usage)

            time.sleep(60)  # Wait for 1 minute before next check
        except Exception as e:
            logging.error("Error in Assurance Module", exc_info=True)
            time.sleep(60)

def notify_operator(cpu_usage, memory_usage):
    message = f"Resource usage is high: CPU Usage: {cpu_usage}%, Memory Usage: {memory_usage}%"
    logging.info("Notifying operator")
    # Send message to GUI (you need to implement /notify_operator in GUI)
    data = {'message': message}
    try:
        response = requests.post(GUI_URL, json=data)
        if response.status_code == 200:
            logging.info("Operator notified successfully")
        else:
            logging.error(f"Failed to notify operator: {response.text}")
    except Exception as e:
        logging.error("Error notifying operator", exc_info=True)

if __name__ == '__main__':
    monitor_usage()

