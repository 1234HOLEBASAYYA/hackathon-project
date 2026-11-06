@echo off
title MEDVISION-AI Master Platform Launcher
cls
echo ======================================================================
echo             MEDVISION-AI ENTERPRISE CLINICAL PLATFORM
echo ======================================================================
echo.

set ROOT_DIR=%~dp0
cd /d "%ROOT_DIR%"

:: 1. Check MongoDB Service
echo [1/5] Verifying MongoDB Database Service...
mongosh --quiet --eval "db.adminCommand('ping')" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo       MongoDB is ACTIVE and responding on port 27017.
) else (
    echo       WARNING: MongoDB did not respond on 127.0.0.1:27017.
    echo       Attempting to start MongoDB Windows service...
    net start MongoDB >nul 2>&1
)

:: 2. Launch Prescription AI Microservice (Port 8001)
echo [2/5] Booting Prescription AI Service on Port 8001...
start "MedVision - Prescription AI (Port 8001)" cmd /k "cd /d %ROOT_DIR%ai-services\prescription-ai && python adapter\service_adapter.py"

:: 3. Launch X-Ray AI Microservice (Port 8002)
echo [3/5] Booting Multi-Region X-Ray AI Service on Port 8002...
start "MedVision - X-Ray AI (Port 8002)" cmd /k "cd /d %ROOT_DIR%ai-services\xray-ai && python adapter\service_adapter.py"

:: 4. Launch CT-Scan AI Microservice (Port 8003)
echo [4/5] Booting CT-Scan Clinical Vision Service on Port 8003...
start "MedVision - CT Scan AI (Port 8003)" cmd /k "cd /d %ROOT_DIR%ai-services\ct-ai && python adapter\service_adapter.py"

:: Wait 4 seconds for AI services to initialize models and bind ports
echo.
echo Waiting 4 seconds for AI model weights and adapters to load...
timeout /t 4 /nobreak >nul

:: 5. Launch Central Express Gateway (Port 3000)
echo [5/5] Booting Central Node.js & Express Gateway on Port 3000...
start "MedVision - Central Express Gateway (Port 3000)" cmd /k "cd /d %ROOT_DIR%backend && npm start"

echo.
echo ======================================================================
echo ALL MEDVISION-AI MICROSERVICES DISPATCHED SUCCESSFULLY!
echo ======================================================================
echo Gateway:        http://localhost:3000
echo Prescription:   http://127.0.0.1:8001
echo X-Ray AI:       http://127.0.0.1:8002
echo CT-Scan AI:     http://127.0.0.1:8003
echo MongoDB:        mongodb://127.0.0.1:27017/medvision_ai
echo.
echo Opening MedVision-AI Clinical Workspace in default browser...
timeout /t 2 /nobreak >nul
start http://localhost:3000
echo.
pause

