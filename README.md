# YOLO Detector — Streamlit Frontend

This repository contains a FastAPI backend that runs a YOLO model and a small Streamlit frontend to upload images and display detected object classes.

Quick start (Windows / PowerShell):

1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the FastAPI backend (from project root):

```powershell
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

4. In a separate terminal, run the Streamlit frontend:

```powershell
streamlit run app.py
```

5. Open the Streamlit UI in your browser (the Streamlit CLI will print the local URL). The backend URL defaults to `http://localhost:8000/detect` in the Streamlit app, change it if your backend runs elsewhere.

Notes:
- The YOLO weights file `yolo11x.pt` must be present in the project root (already included).
- If using Docker, consider exposing port 8000 for the backend and serving Streamlit outside the container or building a multi-service setup.

Render deployment notes
----------------------
If you attempted to deploy on Render and saw an error mentioning `cargo build` or `Cargo.toml` (Rust), Render tried to detect a Rust project. To force Render to use Python and avoid that error, a `render.yaml` is included in the repository which sets the service environment to `python` and specifies the build and start commands.

Steps to deploy on Render:
1. Create a new Web Service on Render and connect your repo.
2. Render should pick up `render.yaml` and run the build/start commands shown there.
3. The service will run `uvicorn server:app --host 0.0.0.0 --port $PORT`.

If you prefer to build via Docker, set `env: docker` in `render.yaml` or provide a Dockerfile (this repo already contains a `Dockerfile`).
