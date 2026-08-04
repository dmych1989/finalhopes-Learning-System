@echo off
cd /d "%~dp0"
set PY=C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe
if not exist "%PY%" (
  echo [ERROR] Python venv not found: %PY%
  echo Please contact support to set up the Python environment.
  pause
  exit /b 1
)
echo Starting Ni Haixia medical query system (web) ...
echo Server will be at http://127.0.0.1:8000
start "" "%PY%" -m uvicorn server:app --host 127.0.0.1 --port 8000
timeout /t 3 >nul
start "" http://127.0.0.1:8000
echo.
echo The server is now running. Close the uvicorn window to stop.
echo (This window can be closed.)
pause
