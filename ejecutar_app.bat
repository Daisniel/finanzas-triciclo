@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title Finanzas del Triciclo - modo desarrollo

echo ========================================
echo Ejecutando Finanzas del Triciclo
echo ========================================
echo.

if not exist "main.py" (
    echo ERROR: No se encontro main.py
    echo Este archivo BAT debe estar dentro de la carpeta del proyecto.
    echo.
    pause
    exit /b 1
)

set "APP_PYTHON="

if exist ".venv\Scripts\python.exe" (
    set "APP_PYTHON=%~dp0.venv\Scripts\python.exe"
    echo Usando el entorno virtual del proyecto.
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: No se encontro Python ni el entorno virtual .venv.
        echo Instala Python o crea el entorno con:
        echo   python -m venv .venv
        echo.
        pause
        exit /b 1
    )
    set "APP_PYTHON=python"
    echo Usando Python del sistema.
)

echo.
echo La consola permanecera abierta para mostrar errores y progreso.
echo Para cerrar la aplicacion, cierra su ventana normalmente.
echo.

"%APP_PYTHON%" -u main.py
set "APP_EXIT=%ERRORLEVEL%"

echo.
if "%APP_EXIT%"=="0" (
    echo La aplicacion termino correctamente.
) else (
    echo La aplicacion termino con el codigo de error %APP_EXIT%.
)
echo.
pause
exit /b %APP_EXIT%
