@echo off:: Start Main Service
echo Starting Main Service on port 8000...
echo Starting OCR services...

:: Set paths relative to script location
set "SCRIPT_DIR=%~dp0"
set "MAIN_PATH=%SCRIPT_DIR%backend\main_app"
set "PADDLE_PATH=%SCRIPT_DIR%backend\ocr_paddle_service"

:: Start Main Service
echo Starting Main Service on port 8000...
start "Main Service" cmd /k "cd %MAIN_PATH% && call venvMain\Scripts\activate.bat && cd .. && set PYTHONPATH=%cd% && cd main_app && uvicorn main:app --reload --port 8000"

:: Wait a moment before starting next service
timeout /t 2 /nobreak > nul

:: Start PaddleOCR Service
echo Starting PaddleOCR Service on port 8001...
start "PaddleOCR Service" cmd /k "cd %PADDLE_PATH% && call venvPaddle310\Scripts\activate.bat && uvicorn app:app --reload --port 8001"

echo.
echo All services have been started!
echo Main Service: http://localhost:8000
echo PaddleOCR Service: http://localhost:8001
echo.
pause
