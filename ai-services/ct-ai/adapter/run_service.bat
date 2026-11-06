@echo off
title MedVision-AI: CT-Scan AI Service (Port 8003)
cd /d "%~dp0\.."
echo Starting CT-Scan AI Service on port 8003...
python adapter\service_adapter.py
pause

