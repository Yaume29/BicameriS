@echo off
setlocal

echo.
echo ========================================
echo   A-ETHERIS - Interface Web (Flask)
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe
    pause
    exit /b 1
)

REM Install dependencies
echo [INFO] Verification des dependances...
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installation de flask...
    pip install flask
)

REM Check LM Studio
echo [INFO] Verification de LM Studio...
curl -s http://localhost:1234/api/v1/models >nul 2>&1
if %errorlevel% neq 0 (
    echo [ATTENTION] LM Studio n'est pas accessible
    echo    Assurez-vous que LM Studio est ouvert et qu'un modele est charge
    echo.
    echo    L'interface demarrera quand meme, mais le chat ne fonctionnera pas.
    echo.
    pause
)

echo [OK] Pret!
echo.
echo ========================================
echo   Demarrage de A-ETHERIS
echo ========================================
echo.
echo Interface accessible a: http://localhost:5000
echo Pour arreter: Ctrl+C
echo.

cd /d "%~dp0ZONE_RESERVEE"
python app.py

echo.
pause