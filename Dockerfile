# ---- Stage 1: build the React frontend ----
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python backend + AI model ----
FROM python:3.12-slim
WORKDIR /app

# System libs needed by torch/Pillow/OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY backend/ ./backend/
COPY ai/ ./ai/
COPY demo_server.py ./
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Built frontend (served by demo_server on the same port)
COPY --from=frontend /app/frontend/dist ./frontend/dist

# Trained YOLOv11 model (custom: smoking + mobile phone)
RUN mkdir -p ai/runs && \
    curl -sL -o ai/runs/best.pt "https://drive.google.com/uc?export=download&id=1aSSMNLgZaIRKAVXW1WHDsUUxmPhjxSj3" && \
    ls -la ai/runs/best.pt

EXPOSE 8000
CMD ["./entrypoint.sh"]
