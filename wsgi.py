"""WSGI 入口 — 供 Gunicorn / 雲端平台（Render、Railway 等）啟動 Flask 應用。

使用方式：
  gunicorn wsgi:app --bind 0.0.0.0:$PORT
"""
import sys
from pathlib import Path

# 將 gvl_app/ 加入 Python 路徑，確保 app.py 可正確匯入 data_handler 等模組
sys.path.insert(0, str(Path(__file__).parent / 'gvl_app'))

from app import app  # noqa: E402
