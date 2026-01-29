FROM python:3.11-slim

WORKDIR /app

# Dépendances système pour OpenCV et ML
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install PyTorch CPU-only first (prevents CUDA downloads)
RUN pip install --no-cache-dir \
    torch \
    torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# Install ultralytics with all its dependencies (CPU-only, no nvidia packages)
RUN pip install --no-cache-dir \
    ultralytics \
    --no-deps

RUN pip install --no-cache-dir \
    numpy>=1.23.0 \
    matplotlib>=3.3.0 \
    pillow>=7.1.2 \
    pyyaml>=5.3.1 \
    requests>=2.23.0 \
    scipy>=1.4.1 \
    tqdm>=4.64.0 \
    pandas>=1.1.4 \
    seaborn>=0.11.0 \
    psutil \
    py-cpuinfo \
    ultralytics-thop>=2.0.0

# Install remaining project dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download YOLO model at build time (avoids runtime download)
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

ENV PYTHONUNBUFFERED=1

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
