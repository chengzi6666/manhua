FROM python:3.12-slim

# 系统依赖：PyMuPDF / pdf_oxide / Pillow 需要的基础库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000
EXPOSE 5000

# 单 worker：app 持有内存态 + sqlite，多进程会串号
# 注意：必须用 shell 形式，JSON 数组不会展开 $PORT 环境变量
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
