
#Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gui_app.py .
COPY templates/ ./templates/

CMD ["python", "gui_app.py"]

