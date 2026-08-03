#!/usr/bin/env bash
# ============================================================
# 大阅读精灵漫画家 - CloudStudio 一键启动脚本
# 用法：在 CloudStudio 工作空间终端执行  bash start_cloudstudio.sh
# ============================================================
set -e

cd "$(dirname "$0")"

echo "===== 1/4 安装依赖（轻量版，不含 torch/rembg/easyocr） ====="
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "===== 2/4 启动服务（gunicorn 单 worker，端口优先读 PORT 环境变量） ====="
export PORT="${PORT:-5000}"
exec gunicorn app:app --bind "0.0.0.0:${PORT}" --workers 1 --timeout 120 --access-logfile - --error-logfile -
