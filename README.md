# Sense - AI Second Brain

This repository contains the source code for the Sense project, separated into backend (backend/) and frontend (frontend/).

## Project Structure

- **Backend (Python)**: Located in `backend/`.
  - `app.py`: Entry point for the FastAPI server.
  - `ai/`, `engine/`, `interfaces/`, `system/`: Core application logic.
  - `store/`: Database and vector store management.

- **Frontend (React)**: Located in `frontend/`.
  - `src/`: React source code.
  - `package.json`: NPM dependencies.
  - `vite.config.js`: Vite configuration.

## Getting Started

### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:
   ```bash
   python app.py
   ```

### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
