.PHONY: all main paddle trocr clean

PYTHON := "C:\Users\Jacob\AppData\Local\Programs\Python\Python310\python.exe"

# Full paths to each component
MAIN_DIR := backend2/main_app
PADDLE_DIR := backend2/ocr_paddle_service
TROCR_DIR := backend2/ocr_trocr_service

MAIN_VENV := $(MAIN_DIR)/venvMain
PADDLE_VENV := $(PADDLE_DIR)/venvPaddle310
TROCR_VENV := $(TROCR_DIR)/venvTrOCR310

all: main # paddle trocr

main:
	@echo "Creating venv for main_app..."
	$(PYTHON) -m venv $(MAIN_VENV)
	. $(MAIN_VENV)/Scripts/activate && pip install --upgrade pip && pip install -r $(MAIN_DIR)/requirements.txt

paddle:
	@echo "Creating venv for paddle service..."
	$(PYTHON) -m venv $(PADDLE_VENV)
	. $(PADDLE_VENV)/Scripts/activate && pip install --upgrade pip
	# Install paddlepaddle-gpu for CUDA 11.8 from paddlepaddle's official wheel URL
	. $(PADDLE_VENV)/Scripts/activate && pip install paddlepaddle-gpu==2.5.0.post118 -f https://www.paddlepaddle.org.cn/whl/windows/mkl/avx/stable.html
	# Install paddleocr separately
	. $(PADDLE_VENV)/Scripts/activate && pip install paddleocr

trocr:
	@echo "Creating venv for TrOCR service..."
	$(PYTHON) -m venv $(TROCR_VENV)
	. $(TROCR_VENV)/Scripts/activate && pip install --upgrade pip && pip install -r $(TROCR_DIR)/requirements.txt

clean:
	@echo "Removing all virtual environments..."
	rm -rf $(MAIN_VENV) $(PADDLE_VENV) $(TROCR_VENV)
