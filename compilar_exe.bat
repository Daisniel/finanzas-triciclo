@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo Compilando Finanzas del Triciclo
echo ========================================
echo.

if not exist "main.py" (
    echo ERROR: No se encontro main.py
    echo El archivo BAT debe estar dentro de la carpeta del proyecto.
    echo.
    pause
    exit /b 1
)

if not exist "logo.ico" (
    echo ERROR: No se encontro logo.ico
    echo Coloca logo.ico en la misma carpeta que este archivo BAT.
    echo.
    pause
    exit /b 1
)

echo Comprobando PyInstaller...
python -m pip install --upgrade pyinstaller

if errorlevel 1 (
    echo.
    echo ERROR: No se pudo instalar o actualizar PyInstaller.
    pause
    exit /b 1
)

echo.
echo Iniciando compilacion...
echo.

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --name "FinanzasTriciclo" ^
    --windowed ^
    --onedir ^
    --icon="logo.ico" ^
    --add-data "logo.ico;." ^
    "main.py"

if errorlevel 1 (
    echo.
    echo ========================================
    echo Ocurrio un error durante la compilacion.
    echo ========================================
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Compilacion terminada correctamente
echo ========================================
echo.
echo El programa se encuentra en:
echo.
echo dist\FinanzasTriciclo\FinanzasTriciclo.exe
echo.
pause