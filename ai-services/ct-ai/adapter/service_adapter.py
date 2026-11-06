"""CT-Scan AI Service Adapter for MEDVISION-AI
Starts the MedVision-AI CT Scan Analysis FastAPI service on port 8003 without modifying
any original files in the ct-ai project.
"""

import os
import sys
from pathlib import Path

# Add project root and backend dir to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import uvicorn
from backend.app.main import app as original_app

PORT = int(os.getenv("CT_SERVICE_PORT", 8003))
HOST = os.getenv("HOST", "127.0.0.1")

def main():
    print(f"\n==========================================================")
    print(f" MEDVISION-AI: CT-Scan AI Microservice")
    print(f" Running on http://{HOST}:{PORT}")
    print(f"==========================================================\n")
    uvicorn.run(original_app, host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()
