FROM python:3.12-slim
WORKDIR /work
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd -u 10001 worker
COPY multipart_copy.py worker.py ./
USER worker
CMD ["gunicorn", "--bind", "0.0.0.0:9000", "--workers", "1", "--threads", "1", "--timeout", "3600", "worker:app"]
