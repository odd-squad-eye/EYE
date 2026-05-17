# app.py — Hugging Face Spaces entry point
# HF Spaces expects app.py at the root, running on port 7860

import uvicorn
from server import app  # noqa: F401 — re-export the FastAPI app

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=7860)
