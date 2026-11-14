FROM m.daocloud.io/docker.io/library/python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir demucs==4.0.1 fastapi==0.115.6 uvicorn==0.34.0 python-multipart==0.0.20 soundfile
ENV OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TORCH_HOME=/data/models
WORKDIR /app
COPY server.py /app/server.py
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","8080"]
