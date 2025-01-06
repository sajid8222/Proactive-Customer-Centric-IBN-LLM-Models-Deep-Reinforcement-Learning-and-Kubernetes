# drl_agent/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY drl_agent.py .

CMD ["python", "drl_agent.py"]
