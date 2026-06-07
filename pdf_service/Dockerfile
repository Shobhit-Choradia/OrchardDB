FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the ONNX model during the build phase so it's baked into the image
RUN python -c "from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2; ONNXMiniLM_L6_V2()"

COPY . .

# Start the Celery worker process (No EXPOSE needed since it doesn't listen on a port)
CMD ["python", "-m", "celery", "-A", "app.worker.celery_app", "worker", "--loglevel=info"]
