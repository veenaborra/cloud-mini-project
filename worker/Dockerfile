FROM python:3.11.10-slim
WORKDIR /app
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY worker/worker.py .
COPY prompts/ prompts/
CMD ["python", "-u", "worker.py"]
