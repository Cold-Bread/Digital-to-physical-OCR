.PHONY: all main paddle frontend clean setup-dev check-python check-node install-node-deps

# Try to detect Python and Node.js
ifeq ($(OS),Windows_NT)
	PYTHON ?= python
	VENV_ACTIVATE = cmd /C "$(VENV_DIR)\Scripts\activate.bat"
	RM_CMD = rmdir /s /q
	PATH_SEP = \
else
	PYTHON ?= python3
	VENV_ACTIVATE = . $(VENV_DIR)/bin/activate
	RM_CMD = rm -rf
	PATH_SEP = /
endif

# Component paths
BACKEND_DIR = backend2
MAIN_DIR = $(BACKEND_DIR)$(PATH_SEP)main_app
PADDLE_DIR = $(BACKEND_DIR)$(PATH_SEP)ocr_paddle_service
FRONTEND_DIR = frontend

# Virtual environment paths
MAIN_VENV = $(MAIN_DIR)$(PATH_SEP)venvMain
PADDLE_VENV = $(PADDLE_DIR)$(PATH_SEP)venvPaddle310

all: check-python check-node main paddle frontend

check-python:
	@$(PYTHON) -c "import sys; assert sys.version_info >= (3,10), 'Python 3.10+ is required'" || (echo "Error: Python 3.10+ is required" && exit 1)

check-node:
	@node -v >/dev/null 2>&1 || (echo "Error: Node.js is required" && exit 1)

main:
	@echo "Setting up main service..."
	$(PYTHON) -m venv "$(MAIN_VENV)"
	$(VENV_ACTIVATE) && pip install -r "$(MAIN_DIR)$(PATH_SEP)requirements.txt"

paddle:
	@echo "Setting up PaddleOCR service..."
	$(PYTHON) -m venv "$(PADDLE_VENV)"
	$(VENV_ACTIVATE) && pip install -r "$(PADDLE_DIR)$(PATH_SEP)requirements.txt"
	@echo "Installing PaddlePaddle..."
	$(VENV_ACTIVATE) && pip install paddlepaddle-gpu>=3.1.0 -i https://mirror.baidu.com/pypi/simple

frontend: check-node install-node-deps
	@echo "Frontend setup complete"

install-node-deps:
	@echo "Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install

clean:
	@echo "Cleaning up virtual environments..."
	-$(RM_CMD) "$(MAIN_VENV)"
	-$(RM_CMD) "$(PADDLE_VENV)"
	@echo "Cleaning up node_modules..."
	-$(RM_CMD) "$(FRONTEND_DIR)$(PATH_SEP)node_modules"

setup-dev: all
	@echo "Setting up development environment..."
	@echo "Installing development tools..."
	cd $(FRONTEND_DIR) && npm install -D typescript @types/react @types/node
	@echo "Development setup complete"
