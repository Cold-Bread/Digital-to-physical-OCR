# Digital-to-Physical OCR System

This project is a comprehensive OCR (Optical Character Recognition) system that uses multiple OCR engines to process images and extract text. It consists of three backend services and a React frontend interface.

## 🌟 Features

- Multiple OCR engines for improved accuracy:
  - PaddleOCR for general text recognition
  - Microsoft's TrOCR for handwritten text
- React + TypeScript frontend for image upload and results display
- FastAPI backend for orchestrating OCR services
- Google Sheets integration for data storage
- Box number tracking system

## 🛠️ Prerequisites

- Python 3.10+ (3.13 recommended)
- Node.js and npm
- Git
- Make (for using the Makefile)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Cold-Bread/Digital-to-physical-OCR.git
cd Digital-to-physical-OCR
```

### 2. Backend Setup

The project uses three separate Python services, each with its own virtual environment. You can set them up using the provided Makefile:

```bash
make all
```

This will create and configure all three virtual environments:
- Main application (FastAPI orchestrator)
- PaddleOCR service
- TrOCR service

Alternatively, you can set up services individually:
```bash
make main      # Setup main FastAPI service
make paddle    # Setup PaddleOCR service
make trocr     # Setup TrOCR service
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## 🏃‍♂️ Running the Application

### 1. Start the Backend Services

You can start all backend services automatically using the provided batch script:

```bash
start_services.bat
```

Simply double-click the `start_services.bat` file in Windows Explorer, or run it from the command prompt.
This will open three separate command prompt windows, each running one of the services:
- Main Service (port 8000)
- PaddleOCR Service (port 8001)
- TrOCR Service (port 8002)

Alternatively, you can start each service manually by opening three separate terminal windows and activating each virtual environment:

Main Service:
```bash
cd backend2/main_app
./venvMain/Scripts/activate  # On Windows
uvicorn main:app --reload --port 8000
```

PaddleOCR Service:
```bash
cd backend2/ocr_paddle_service
./venvPaddle310/Scripts/activate  # On Windows
uvicorn app:app --reload --port 8001
```

TrOCR Service:
```bash
cd backend2/ocr_trocr_service
./venvTrOCR310/Scripts/activate  # On Windows
uvicorn app:app --reload --port 8002
```

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:5173

## 📝 API Endpoints

### Main Service (port 8000)

- `GET /` - Health check
- `GET /box/{box_number}` - Get patients from a specific box
- `GET /process-image` - Process an image through all OCR engines
- `POST /update-records` - Update patient records

### PaddleOCR Service (port 8001)

- `POST /ocr` - Process image with PaddleOCR

### TrOCR Service (port 8002)

- `POST /ocr` - Process image with TrOCR (optimized for handwriting)

## ✅ Quick Commands Summary

| Task                  | Command                                           |
|----------------------|--------------------------------------------------|
| Setup All Services   | `make all`                                        |
| Setup Main Service   | `make main`                                       |
| Setup PaddleOCR      | `make paddle`                                     |
| Setup TrOCR          | `make trocr`                                      |
| Clean All            | `make clean`                                      |
| Start Frontend       | `cd frontend && npm run dev`                      |

## 🧹 Cleanup

To remove all virtual environments and start fresh:

```bash
make clean
```

## 🔧 Configuration

### Google Sheets Integration

1. Place your Google Sheets credentials in:
   ```
   backend2/main_app/config/credentials.json
   ```
2. Configure sheet settings in:
   ```
   backend2/main_app/config/sheets_config.py
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
