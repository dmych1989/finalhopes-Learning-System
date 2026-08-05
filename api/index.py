# -*- coding: utf-8 -*-
"""Vercel serverless entry (ASGI).

`app` is a top-level name imported from server so Vercel detects the handler.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.abspath(os.path.join(HERE, "..", "web_app"))
sys.path.insert(0, WEB)

from server import app  # noqa: E402
