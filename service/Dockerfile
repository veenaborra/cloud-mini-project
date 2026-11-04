# Build from the repo root:  docker build -f service/Dockerfile -t cmd-parser:1.0 .
# No model weights in the image: the model is downloaded from object storage at start-up.
FROM python:3.11.10-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HUB_OFFLINE=1
WORKDIR /app
COPY service/requirements.txt .
RUN pip install -r requirements.txt
COPY service/app.py service/inference.py ./
COPY data/schema.json ./schema.json
RUN useradd --uid 10001 --create-home appuser
USER 10001
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
