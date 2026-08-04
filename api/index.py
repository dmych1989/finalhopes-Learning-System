# -*- coding: utf-8 -*-
"""Vercel serverless entry (ASGI).

The FastAPI app lives in web_app/server.py. We add web_app to sys.path and
re-export its `app`. Data is read from web_app/data.db (SQLite) — no pyodbc /
Access ODBC driver needed, so this runs on Vercel's Linux runtime.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "..", "web_app")
sys.path.insert(0, os.path.abspath(WEB))

from server import app  # noqa: E402

# Vercel's Python runtime expects an ASGI callable named `app`.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
