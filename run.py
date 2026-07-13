#!/usr/bin/env python3
"""
YT Comment AI Analytics — Launch Script
Starts the Python backend (FastAPI) on port 8000.
The PHP frontend is started separately via start.bat or `npm start`.
"""
import sys
import subprocess
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

print("""
    ╔══════════════════════════════════════════════════╗
    ║   YT Comment AI Analytics Engine  v2.0           ║
    ║   Backend: FastAPI + FAISS + Ollama              ║
    ║   Frontend: PHP (run separately via start.bat)   ║
    ╚══════════════════════════════════════════════════╝
""")

venv_python = None

# Check for .venv
venv_dir = BASE_DIR / ".venv"
if sys.platform == "win32":
    venv_python = venv_dir / "Scripts" / "python.exe"
else:
    venv_python = venv_dir / "bin" / "python"

if not venv_python.exists():
    print("[setup] Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    print("[setup] Installing requirements...")
    subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt", "--quiet"], check=True)
    print("[setup] Done.")

print("[+] Starting FastAPI backend on http://localhost:8000 ...")
print("[+] PHP frontend runs separately: cd frontend && npm start (or start.bat)")
print("[+] Press Ctrl+C to stop backend\n")

try:
    subprocess.run(
        [str(venv_python), "-m", "uvicorn", "backend.main:app",
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(BASE_DIR),
    )
except KeyboardInterrupt:
    print("\n[+] Backend stopped.")
