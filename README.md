
# Proactive-Customer-Centric-IBN-LLM-Models-Deep-Reinforcement-Learning-and-Kubernetes

## Overview

This project integrates advanced technologies to optimize resource management in a Kubernetes environment. It dynamically adjusts computing resources based on user intents and real-time system performance, enhancing efficiency and responsiveness. The system is composed of several interconnected modules: 

- **GUI for User Interaction**
- **LLM Translation Engine**
- **Resource Orchestration Module**
- **Assurance Module**
- **Deep Reinforcement Learning (DRL) Agent**
- **Monitoring Tools (Prometheus & Grafana)**

## Key Features

- **Intent-Based Management:** Users submit high-level intents through the GUI, such as scaling replicas or increasing CPU allocation for applications.
- **LLM Translation Engine:** Converts user intents into actionable Kubernetes policies.
- **Dynamic Resource Allocation:** The DRL Agent optimizes resource usage based on system performance and predefined policies.
- **Proactive Monitoring:** Assurance Module ensures system reliability by monitoring metrics and dynamically adapting to changing conditions.
- **Visualization Tools:** Prometheus and Grafana provide insights into system performance and resource utilization.

## System Workflow

1. **User Intents Submission:** Users submit intents via the GUI, specifying high-level goals for resource management.
2. **Intent Translation:** The LLM Translation Engine interprets intents and translates them into actionable policies.
3. **Resource Orchestration:** The Resource Orchestration Module applies the policies to the Kubernetes cluster, adjusting configurations like deployments or resource quotas.
4. **Performance Assurance:** The Assurance Module monitors resource usage via Prometheus, triggering new intents if thresholds are exceeded.
5. **Optimization via DRL Agent:** The DRL Agent fine-tunes resource allocation in real-time to maximize efficiency while adhering to policy constraints.
6. **Monitoring & Visualization:** Prometheus collects metrics, and Grafana provides visual dashboards for system insights.

## Components

- **DRL Agent:** Reinforcement learning-based optimization of resource allocation.
- **GUI:** Intuitive interface for submitting user intents.
- **LLM Translation Engine:** Translates intents into actionable Kubernetes policies.
- **Assurance Module:** Monitors system performance and ensures adaptability.
- **Monitoring Tools:** Prometheus and Grafana for metrics collection and visualization.

## Prerequisites

- Kubernetes cluster
- Docker
- Prometheus & Grafana
- Python 3.8 or higher
- Required Python packages (listed in `requirements.txt`)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/Proactive-Customer-Centric-IBN-LLM-Models-Deep-Reinforcement-Learning-and-Kubernetes.git
   ```
2. Navigate to the project directory:
   ```bash
   cd Proactive-Customer-Centric-IBN-LLM-Models-Deep-Reinforcement-Learning-and-Kubernetes
   ```
3. Set up the Kubernetes cluster and install Prometheus and Grafana.
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Deploy the application:
   ```bash
   kubectl apply -f app_deployment.yaml
   kubectl apply -f app_service.yaml
   ```

## Usage

1. Start the application.
2. Access the GUI to submit user intents.
3. Monitor the system performance via Grafana dashboards.
4. Observe the dynamic resource adjustments and system adaptations.

## Directory Structure

- `DRL_agent/`: Contains the reinforcement learning agent code.
- `GUI/`: Frontend code for the graphical user interface.
- `LLM_Env/`: Implementation of the LLM Translation Engine.
- `Monitoring/`: Scripts for Prometheus and Grafana integration.
- `assurance_module/`: Code for monitoring and ensuring system reliability.
- `customer_apps/`: Sample applications for testing resource orchestration.
- `app_deployment.yaml`: Kubernetes deployment configuration.
- `app_service.yaml`: Kubernetes service configuration.

## Monitoring Tools

- **Prometheus:** Collects metrics for monitoring system performance.
- **Grafana:** Visualizes metrics for decision-making and troubleshooting.

## Contributions

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes and push to your branch.
4. Submit a pull request.
