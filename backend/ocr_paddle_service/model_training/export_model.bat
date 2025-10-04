@echo off
REM PaddleOCR Model Export Script for Windows
echo Starting PaddleOCR model export...

REM Navigate to PaddleOCR directory  
cd /d "C:\Users\Jacob\Personal Projects\Digital-to-physical-OCR\backend\ocr_paddle_service\model_training\PaddleOCR"

REM Activate training environment if available
if exist "..\training_venv\Scripts\activate.bat" (
    echo Activating training environment...
    call "..\training_venv\Scripts\activate.bat"
)

REM Export the model
echo Exporting model...
python tools\export_model.py ^
    -c "C:\Users\Jacob\Personal Projects\Digital-to-physical-OCR\backend\ocr_paddle_service\model_training\export_config.yml" ^
    -o Global.pretrained_model="C:\Users\Jacob\Personal Projects\Digital-to-physical-OCR\backend\ocr_paddle_service\model_training\training_output\rec_models\best_accuracy" ^
       Global.save_inference_dir="C:\Users\Jacob\Personal Projects\Digital-to-physical-OCR\backend\ocr_paddle_service\models\custom_trained_v3"

echo Export completed!
echo Check output in: C:\Users\Jacob\Personal Projects\Digital-to-physical-OCR\backend\ocr_paddle_service\models\custom_trained_v3\
pause
