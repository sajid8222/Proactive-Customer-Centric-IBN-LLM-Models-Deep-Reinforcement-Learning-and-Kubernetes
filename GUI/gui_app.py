# # gui/gui_app.py
# from flask import Flask, request, jsonify, render_template
# import requests

# app = Flask(__name__)

# # Update to use the fully qualified domain name within the cluster
# # gui/gui_app.py
# LLM_TRANSLATION_ENGINE_URL = "http://llm-service.sagin-network.svc.cluster.local:8080/translate_intent"

# messages = []

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         intent = request.form['intent']
#         try:
#             response = requests.post(LLM_TRANSLATION_ENGINE_URL, json={'intent': intent})
#             if response.status_code == 200:
#                 policy = response.json().get('policy')
#                 message = response.json().get('message', '')
#                 return render_template('index.html', policy=policy, message=message, messages=messages)
#             else:
#                 error = response.json().get('error', 'Unknown error')
#                 return render_template('index.html', error=error, messages=messages)
#         except requests.exceptions.RequestException as e:
#             error = f"Error communicating with LLM: {e}"
#             return render_template('index.html', error=error, messages=messages)
#     return render_template('index.html', messages=messages)

# @app.route('/notify_operator', methods=['POST'])
# def notify_operator():
#     data = request.json
#     message = data.get('message', '')
#     messages.append(message)
#     return jsonify({'status': 'Operator notified'}), 200

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)


# gui_app.py
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

LLM_TRANSLATION_ENGINE_URL = "http://localhost:8080/translate_intent"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_intent', methods=['POST'])
def submit_intent():
    intent = request.form.get('intent')
    response = requests.post(LLM_TRANSLATION_ENGINE_URL, json={'intent': intent})
    if response.status_code == 200:
        return jsonify({'status': 'success', 'data': response.json()})
    else:
        return jsonify({'status': 'error', 'message': response.text}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
