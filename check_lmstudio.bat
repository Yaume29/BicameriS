@echo off
setlocal

echo.
echo ========================================
echo   AETHERIS - Verification LM Studio
echo ========================================
echo.

curl -s http://localhost:1234/api/v1/models >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] LM Studio n'est pas accessible
    echo Assure-toi que:
    echo   1. LM Studio est ouvert
    echo   2. L'API Server est activ‚ dans les settings
    echo   3. Un modŠle est charg‚
    pause
    exit /b 1
)

echo [OK] LM Studio est accessible
echo.

echo available Models:
echo =================
python -c "import sys,json; 
data=json.load(sys.stdin); 
for m in data.get('data',[]):
    loaded = '(*) CHARGE' if m.get('loaded_instances') else '   '
    print(f'{loaded} {m[\"display_name\"]}')" < nul 2>nul

curl -s http://localhost:1234/api/v1/models

echo.
pause