# 📁 Full Stack App Setup Guide

This project consists of a **FastAPI** backend and a **React + Vite** frontend. Follow the steps below to set everything up locally.

---

## 📦 Backend Setup (FastAPI + Python)

1. Navigate to the backend folder:
   ```bash
   cd backend
   ```

2. Create a virtual environment to isolate dependencies:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - On **Mac/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the FastAPI server with hot-reloading:
   ```bash
   uvicorn main:app --reload
   ```

- API will be live at: [http://localhost:8000](http://localhost:8000)
- Interactive docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 🧪 Python Virtual Environment Notes

A virtual environment (`venv`) is used to keep this project's Python dependencies isolated from the global environment. This prevents version conflicts and ensures reproducibility. Always activate the venv before installing packages or running the backend.

---

## 💻 Frontend Setup (React + Vite + TypeScript)

1. Ensure Node.js is installed:  
   👉 [Download Node.js](https://nodejs.org/en/download)

2. Navigate to the frontend folder:
   ```bash
   cd frontend
   ```

3. Install frontend dependencies:
   ```bash
   npm install
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```

- Frontend will be live at: [http://localhost:5173](http://localhost:5173)
- Vite supports hot reload; changes will reflect instantly.
- To build for production:
   ```bash
   npm run build
   ```

---

## ✅ Quick Commands Summary

| Task             | Command                                      |
|------------------|----------------------------------------------|
| Start Backend    | `uvicorn backend.main:app --reload`          |
| Start Frontend   | `cd frontend && npm run dev`                 |
| Build Frontend   | `npm run build` (from `frontend` folder)     |

