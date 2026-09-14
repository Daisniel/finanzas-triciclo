@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "APP_PYTHON="
if exist ".venv\Scripts\python.exe" (
    set "APP_PYTHON=%~dp0.venv\Scripts\python.exe"
) else (
    set "APP_PYTHON=python"
)

"%APP_PYTHON%" scripts\reset_demo.py
if errorlevel 1 pause & exit /b 1
"%APP_PYTHON%" -u main.py
set "APP_EXIT=%ERRORLEVEL%"
pause
exit /b %APP_EXIT%
