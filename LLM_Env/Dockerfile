# llm_translation_engine/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY llm_translation_engine.py .

CMD ["python", "llm_translation_engine.py"]
