# llm_translation_engine.py
from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

NS3_SCRIPT_PATH = "./ns3_simulation.py"

@app.route('/translate_intent', methods=['POST'])
def translate_intent():
    data = request.get_json()
    intent = data.get('intent')
    if not intent:
        return jsonify({'error': 'No intent provided'}), 400

    # Translate intent to network configuration
    network_config = translate_to_config(intent)

    # Run ns3 simulation
    simulation_result = run_ns3_simulation(network_config)

    return jsonify({
        'network_config': network_config,
        'simulation_result': simulation_result
    })

def translate_to_config(intent):
    # Implement your translation logic here
    # For example, parse the intent and create a config dictionary
    config = {
        "bandwidth": "increase",
        "nodes": {
            "satellite": {"id": 0, "location": "Satellite 0"},
            "ground": {"id": 0, "location": "Ground Node 0"}
        },
        "resources": {
            "vCPUs": 2,
            "memory": "4GB"
        }
    }
    return config

def run_ns3_simulation(config):
    try:
        result = subprocess.run(
            ["python", NS3_SCRIPT_PATH, json.dumps(config)],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
