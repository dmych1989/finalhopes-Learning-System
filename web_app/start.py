#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
人纪/医学查询系统 本地启动器
- 自动切换工作目录到本脚本所在目录（web_app）
- 若当前 Python 未安装 uvicorn/fastapi/cnlunar，自动 pip 安装
- 启动 uvicorn，监听 http://127.0.0.1:8000
双击或在命令行运行即可：  python start.py
"""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)


def ensure_deps():
    try:
        import uvicorn  # noqa: F401
        import fastapi  # noqa: F401
        import cnlunar  # noqa: F401
    except ImportError:
        print("[start] 检测到缺少依赖，正在安装 fastapi uvicorn cnlunar ...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "fastapi", "uvicorn", "cnlunar"]
        )


def main():
    ensure_deps()
    print("[start] 工作目录:", os.getcwd())
    print("[start] 启动 uvicorn -> http://127.0.0.1:8000  (Ctrl+C 退出)")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "server:app",
         "--host", "127.0.0.1", "--port", "8000", "--reload"],
    )


if __name__ == "__main__":
    main()
