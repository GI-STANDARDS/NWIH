@echo off
echo ============================================
echo   YT Comment AI Analytics - Full System
echo ============================================
echo.
echo Starting backend (Python FastAPI) on port 8000...
echo Starting frontend (PHP) on port 8080...
echo.
echo Access the app at: http://localhost:8080
echo.
start "YT Backend" cmd /c "python run.py"
cd frontend
start "YT Frontend" cmd /c "php -S localhost:8080 -t ."
cd ..
timeout /t 5 /nobreak >nul
start http://localhost:8080
echo.
echo Browser should open automatically. If not, visit http://localhost:8080
echo Close windows with Ctrl+C.
pause
