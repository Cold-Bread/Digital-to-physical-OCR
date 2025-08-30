.PHONY: all main paddle trocr clean

PYTHON := "C:\Users\jacob\AppData\Local\Programs\Python\Python313\python.exe"

# Full paths to each component
MAIN_DIR := backend2\main_app
PADDLE_DIR := backend2\ocr_paddle_service
TROCR_DIR := backend2\ocr_trocr_service

MAIN_VENV := $(MAIN_DIR)\venvMain
PADDLE_VENV := $(PADDLE_DIR)\venvPaddle310
TROCR_VENV := $(TROCR_DIR)\venvTrOCR310

all: main paddle trocr

main:
	@echo "Creating venv for main_app..."
	$(PYTHON) -m venv "$(MAIN_VENV)"
	cmd /C ""$(MAIN_VENV)\Scripts\activate.bat" && pip install -r "$(MAIN_DIR)\requirements.txt""

paddle:
	@echo "Creating venv for paddle service..."
	$(PYTHON) -m venv "$(PADDLE_VENV)"
	cmd /C ""$(PADDLE_VENV)\Scripts\activate.bat" && pip install paddlepaddle-gpu==3.1.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/ && pip install -r "$(PADDLE_DIR)\requirements.txt""

trocr:
	@echo "Creating venv for TrOCR service..."
	$(PYTHON) -m venv "$(TROCR_VENV)"
	cmd /C ""$(TROCR_VENV)\Scripts\activate.bat" && pip install -r "$(TROCR_DIR)\requirements.txt""

clean:
	@echo "Removing all virtual environments..."
	cmd /C "if exist "$(MAIN_VENV)" rmdir /s /q "$(MAIN_VENV)""
	cmd /C "if exist "$(PADDLE_VENV)" rmdir /s /q "$(PADDLE_VENV)""
	cmd /C "if exist "$(TROCR_VENV)" rmdir /s /q "$(TROCR_VENV)""
