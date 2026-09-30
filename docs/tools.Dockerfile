FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends weasyprint poppler-utils && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir markdown==3.10.2 pypdf==6.9.1 pillow==12.2.0
WORKDIR /repo
