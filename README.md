# Digital-to-Physical OCR System

A powerful OCR (Optical Character Recognition) system that combines multiple OCR engines to accurately process and extract text from both printed and handwritten documents. Perfect for digitizing physical records and managing patient data with box tracking capabilities.

## 🌟 Key Features

- **Dual OCR Engine System**:
  - PaddleOCR - Optimized for printed text
  - Advanced handwriting recognition
- **Modern Tech Stack**:
  - React + TypeScript frontend with real-time processing
  - FastAPI backend for high-performance API handling
  - Google Sheets integration for secure data storage
- **Smart Processing**:
  - Automatic text classification (printed vs handwritten)
  - Advanced name matching algorithms
  - Intelligent date format handling
- **User-Friendly Interface**:
  - Drag-and-drop image upload
  - Real-time OCR results display
  - Easy data editing and validation
  - Box tracking system for physical records

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: 3.10 or higher (3.13 recommended)
  - Check with: `python --version`
- **Node.js**: Latest LTS version
  - Check with: `node --version`
- **Package Managers**:
  - pip (comes with Python)
  - npm (comes with Node.js)
- **Build Tools**:
  - Git
  - Make (for automated setup)
  
### Optional but Recommended
- CUDA-compatible GPU for faster OCR processing
- Visual Studio Code for development

## 🚀 Installation

Follow these steps to get the system up and running:

### 1. Get the Code

```bash
# Clone the repository
git clone https://github.com/Cold-Bread/Digital-to-physical-OCR.git
cd Digital-to-physical-OCR
```

### 2. Easy Setup (Recommended)

The easiest way to set up everything is using our automated setup:

```bash
# This will set up everything: backend services, frontend, and development tools
make all
```

This command will:
1. Check Python and Node.js requirements
2. Set up all Python virtual environments
3. Install PaddleOCR and its dependencies
4. Set up the React frontend
5. Configure development tools

### 3. Manual Setup (Alternative)

If you prefer more control, you can set up components individually:

```bash
# Set up the main orchestrator service
make main

# Set up the PaddleOCR service
make paddle

# Set up the frontend
make frontend

# Set up development environment
make setup-dev
```

### 4. GPU Support (Optional)

By default, the system is configured to use GPU for better performance. If you don't have a CUDA-compatible GPU:

1. Edit `requirements_full.txt`
2. Comment out `paddlepaddle-gpu>=3.1.0`
3. Uncomment `# paddlepaddle>=3.1.0`
4. Run `make clean` followed by `make all`

## 🏃‍♂️ Running the Application

### 1. Quick Start (Recommended)

On Windows, simply use the provided batch script:

```bash
start_services.bat
```

This will:
- Start all backend services automatically
- Open browser with the frontend interface
- Configure all necessary ports

### 2. Manual Start

If you prefer more control or are on a different OS, start the services manually:

#### Backend Services

Open three separate terminals and run:

```bash
# Terminal 1 - Main Service (Port 8000)
cd backend2/main_app
source venvMain/Scripts/activate  # Windows: .\venvMain\Scripts\activate
uvicorn main:app --reload --port 8000

# Terminal 2 - PaddleOCR Service (Port 8001)
cd backend2/ocr_paddle_service
source venvPaddle310/Scripts/activate  # Windows: .\venvPaddle310\Scripts\activate
uvicorn app:app --reload --port 8001
```

#### Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- API Documentation: http://localhost:8000/docs
- PaddleOCR Service: http://localhost:8001/docs

### 3. First-Time Setup

Before running the application for the first time:

1. Configure Google Sheets:
   ```bash
   # Place your credentials file here
   backend2/main_app/config/credentials.json
   ```

2. Configure sheet settings:
   ```python
   # Edit as needed
   backend2/main_app/config/sheets_config.py
   ```

## 📝 API Documentation

### Main Orchestrator (Port 8000)
| Endpoint | Method | Description |
|----------|---------|------------|
| `/` | GET | Health check |
| `/box/{box_number}` | GET | Retrieve patient records from a box |
| `/process-image` | POST | Process image through OCR pipeline |
| `/update-records` | POST | Update patient records |

### PaddleOCR Service (Port 8001)
| Endpoint | Method | Description |
|----------|---------|------------|
| `/ocr` | POST | Process image with PaddleOCR |

Full API documentation available at:
- Main API: http://localhost:8000/docs
- PaddleOCR: http://localhost:8001/docs

## ⚙️ Available Commands

### Setup Commands
| Command | Description |
|---------|-------------|
| `make all` | Set up entire project (recommended) |
| `make setup-dev` | Set up development environment |
| `make frontend` | Set up frontend only |
| `make paddle` | Set up PaddleOCR service |
| `make main` | Set up main service |
| `make clean` | Remove all environments |

### Run Commands
| Command | Description |
|---------|-------------|
| `start_services.bat` | Start all services (Windows) |
| `npm run dev` | Start frontend development server |
| `uvicorn main:app --port 8000` | Start main service |

## 🔧 Configuration Guide

### 1. Google Sheets Setup

1. Get credentials:
   - Go to Google Cloud Console
   - Create a new project
   - Enable Google Sheets API
   - Create service account
   - Download credentials

2. Configure credentials:
   ```bash
   # Place credentials file here
   backend2/main_app/config/credentials.json
   ```

3. Configure settings:
   ```python
   # Edit sheet settings
   backend2/main_app/config/sheets_config.py
   ```

### 2. Environment Setup

The system uses Python virtual environments to manage dependencies:

```bash
# Rebuild environments
make clean
make all

# Update dependencies
pip install -r requirements_full.txt
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Run tests if available
5. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

## 🧹 Maintenance

To keep the system running smoothly:

1. Regular cleanup:
   ```bash
   make clean  # Remove all virtual environments
   ```

2. Update dependencies:
   ```bash
   pip list --outdated  # Check for updates
   ```

3. Monitor logs:
   ```bash
   # Main service logs
   backend2/main_app/logs/
   
   # PaddleOCR logs
   backend2/ocr_paddle_service/logs/
   ```
