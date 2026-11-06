@echo off
title MedVision-AI: Prescription AI Service (Port 8001)
cd /d "%~dp0\.."
echo Starting Prescription AI Service on port 8001...
python adapter\service_adapter.py
pause

