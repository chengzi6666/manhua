FROM python:3.12-slim

# 系统依赖：PyMuPDF / pdf_oxide / Pillow 需要的基础库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 tesseract-ocr \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000
ENV VIDEO_SHARE_STORAGE_ROOT=/data/video_shares
EXPOSE 5000

# 单 worker：app 持有内存态 + sqlite，多进程会串号
# 必须显式 sh -c 包裹：Railway 容器运行时不会自动展开 $PORT，
# 直接 CMD gunicorn ... 会把字面量 "$PORT" 传给 gunicorn 导致 healthcheck 失败
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-3000} --workers 1 --timeout 600"]
