@echo off
title MedVision-AI: Multi-Region X-Ray AI Service (Port 8002)
cd /d "%~dp0\.."
echo Starting X-Ray AI Service on port 8002...
python adapter\service_adapter.py
pause

