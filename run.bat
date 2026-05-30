@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" app.py
) else (
  python app.py
)

pause
