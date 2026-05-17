---
title: EYE - AI Vision Assistant
emoji: 👁️
colorFrom: gray
colorTo: black
sdk: docker
app_port: 7860
---

# EYE — AI Vision Assistant

A distraction-free, gesture-controlled AI assistant that describes what your phone camera sees. Designed as an assistive tool for visually impaired users.

## How It Works

| Gesture | Mobile | Desktop | Action |
|---------|--------|---------|--------|
| **Single tap** | Tap screen | Click | Quick YOLO summary ("I see a person nearby on your left") |
| **Double tap** | Double tap | Double click | Detailed Florence-2 scene description |
| **Two-finger tap** | 2-finger tap | Right-click | Silence the AI for 5 seconds |
| **Long press** | Hold 600ms | Middle click | Repeat last spoken text |

## Models Used

| Model | Size | Purpose |
|-------|------|---------|
| **YOLOv10-nano** (ONNX) | 10 MB | Real-time object detection with spatial awareness |
| **Florence-2-base** (HuggingFace) | ~450 MB | Detailed scene captioning on demand |

## Architecture

```
Phone Camera → Tap Screen → Capture 1 Frame → POST /api/tell or /api/more → AI Response → Text-to-Speech
```

- **No WebSockets** — Simple REST endpoints (`POST /api/tell`, `POST /api/more`)
- **No Voice Commands** — Touch gestures only (works in noisy environments)
- **No Streaming** — Camera stays local, only sends a frame when you tap

## Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
fastapi dev server.py

# Open http://localhost:8000 on your laptop or phone (same network)
```

## Deploy to Hugging Face Spaces

1. Create a new Space with **Docker** SDK
2. Push this repo (includes `Dockerfile` and `app.py`)
3. The nano YOLO model (`yolo26n.onnx`, 10MB) is included in the repo
4. Florence-2 downloads automatically on first launch

## Project Structure

```
├── server.py            # FastAPI backend (REST endpoints)
├── app.py               # HF Spaces entry point
├── onnx_detector.py     # YOLOv10-nano ONNX inference
├── florence_server.py   # Florence-2 captioning (single-pass)
├── static/
│   ├── script.js        # Gesture system + REST API calls
│   └── style.css        # Pitch-black UI
├── templates/
│   └── index.html       # Minimal HTML shell
├── yolo26n.onnx         # YOLO nano model (10MB)
├── Dockerfile           # Container config for HF Spaces
└── requirements.txt     # Python dependencies
```
