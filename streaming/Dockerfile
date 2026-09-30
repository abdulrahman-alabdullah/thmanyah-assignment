FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir boto3==1.43.59
WORKDIR /work
COPY encode.sh render-config.py ./
RUN chmod +x encode.sh
CMD ["./encode.sh"]
