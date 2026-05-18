---
title: EYE - AI Vision Assistant
colorFrom: gray
colorTo: gray
sdk: docker
app_port: 7860
---

<div align="center">

# EYE — AI Vision Assistant

**See the world through sound.**

An AI-powered assistive tool that turns your phone camera into a real-time audio narrator — built for visually impaired users, usable by anyone.

[![Live Demo](https://img.shields.io/badge/Live_Demo-Hugging_Face-yellow?style=for-the-badge)](https://huggingface.co/spaces/sudo-raj-1/final_eye)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-green?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

</div>

---

## What is EYE?

EYE is a **gesture-controlled AI assistant** that uses your phone's camera to describe the world around you — entirely through audio. No visual UI, no buttons to find, no screen to read.

- **Tap once** — instant object detection ("I see a person nearby on your left")
- **Tap twice** — rich scene description ("A person standing in a park with trees and a bench")
- **Works anywhere** — noisy streets, quiet rooms, indoors or outdoors

> **Why gestures instead of voice commands?** Voice recognition fails in noisy environments — the exact places where a visually impaired user needs assistance most. Simple touch gestures work 100% of the time, everywhere.

---

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Phone Camera │────>│  Tap Screen  │────>│  Capture 1 Frame │────>│    REST API      │
└─────────────┘     └──────────────┘     └──────────────────┘     │  POST /api/tell  │
                                                                   │  POST /api/more  │
                                                                   └────────┬─────────┘
                                                                            │
                                                            ┌───────────────┴───────────────┐
                                                            │                               │
                                                      ┌─────┴─────┐                 ┌───────┴───────┐
                                                      │  YOLOv26-X │                 │ Florence-2-L  │
                                                      │  (~100ms)  │                 │ (~5-15s)      │
                                                      └─────┬─────┘                 └───────┬───────┘
                                                            │                               │
                                                            v                               v
                                                     "I see a person             "A woman walking her
                                                      nearby on your              dog along a tree-lined
                                                      left."                      sidewalk in the evening."
                                                            │                               │
                                                            └───────────┬───────────────────┘
                                                                        v
                                                                Text-to-Speech
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **ONNX Runtime, not Ultralytics** | Ultralytics wraps YOLO in heavy Python preprocessing — ONNX Runtime runs the model directly through its C++ backend, cutting inference overhead and eliminating a ~700 MB dependency |
| **REST, not WebSockets** | Simpler, more reliable — no persistent connection to manage or reconnect |
| **Touch gestures, not voice** | Works in noisy environments where voice recognition fails |
| **No camera streaming** | Camera stays local; only sends a single frame when you tap (privacy + bandwidth) |
| **Black screen UI** | No visual elements to distract — the entire interface is audio |
| **Scene caching** | If the scene hasn't changed (MSE < 1500), returns cached description instantly |

---

## Controls

### Mobile (Primary)

| Gesture | Action |
|---------|--------|
| **Tap** | Quick scan — YOLO detects objects, tells you what's nearby and where |
| **Double tap** | Deep look — Florence-2 describes the full scene in natural language |
| **Two-finger tap** | Mute the assistant for 5 seconds |
| **Long press** (600ms) | Repeat the last spoken response |

### Desktop (Development / Testing)

| Input | Action |
|-------|--------|
| **Click** | Quick scan (same as tap) |
| **Double click** | Deep look (same as double tap) |
| **Right-click** | Mute for 5 seconds |
| **Middle-click** | Repeat last response |

---

## Models

| Model | Parameters | Size | Speed (CPU) | Role |
|-------|-----------|------|-------------|------|
| [YOLOv26-X](https://github.com/THU-MIG/yolov10) | 56M | 223 MB | ~50-200ms | Object detection with spatial awareness (direction + distance) |
| [Florence-2-large](https://huggingface.co/microsoft/Florence-2-large) | 770M | ~1.5 GB | ~5-15s | Natural-language scene captioning |

### Why Two Models?

**YOLO** is fast but shallow — it tells you *what* objects exist and *where* they are relative to you. **Florence-2** is slow but deep — it understands the full *scene* and describes it like a human would. Together, they give instant spatial awareness (tap) and detailed understanding (double tap).

---

## Getting Started

### Prerequisites

- Python 3.11+
- A webcam or phone camera
- ~2 GB disk space (for model downloads)

### Local Development

```bash
# Clone the repository
git clone https://github.com/odd-squad-eye/EYE.git
cd EYE
git checkout proto-2

# Install dependencies
pip install -r requirements.txt

# Start the server
python server.py

# Open in your browser
#   Laptop:  http://localhost:8000
#   Phone:   http://<your-laptop-ip>:8000  (same Wi-Fi network)
```

> **Mobile usage:** Open the URL in Chrome or Safari, tap "Start", and allow camera and microphone permissions. The screen will go black — that is by design. The entire interface is audio-driven.

### Deploying to Hugging Face Spaces

1. Create a new Space and select **Docker** as the SDK
2. Push this repository (the included `Dockerfile` handles everything)
3. The YOLO model is bundled in the repo; Florence-2 downloads automatically on first launch

---

## Project Structure

```
EYE/
├── server.py              # FastAPI backend — REST endpoints, request routing,
│                          # thread pool management, scene-change detection
│
├── onnx_detector.py       # YOLO inference — letterbox preprocessing, ONNX Runtime,
│                          # spatial awareness (direction + distance from bounding boxes)
│
├── florence_server.py     # Florence-2 inference — model loading with CPU-safe attention,
│                          # single-pass detailed captioning
│
├── static/
│   ├── script.js          # Client — gesture recognition (tap/double-tap/long-press),
│   │                      # camera capture, REST API calls, text-to-speech
│   └── style.css          # Pitch-black UI (intentionally minimal)
│
├── templates/
│   └── index.html         # Minimal HTML shell (video + canvas + overlay)
│
├── yolo26n.onnx           # YOLOv26 nano model (10 MB, fallback)
├── yolo26x.onnx           # YOLOv26 X model (223 MB, primary)
├── Dockerfile             # Production container (Python 3.11-slim + flash_attn stub)
├── requirements.txt       # Python dependencies
└── LICENSE                # MIT
```

---

## API Reference

### `POST /api/tell`

Fast object detection with spatial context. Designed for frequent, low-latency calls.

**Request:** `multipart/form-data` with a `file` field (JPEG image)

**Response:**
```json
{
  "summary": "I see a person very close in front of you and a car nearby on your left."
}
```

**Typical latency:** 50–200ms

---

### `POST /api/more`

Detailed scene captioning powered by Florence-2. Includes scene-change caching — if the scene hasn't changed significantly since the last call, the cached result is returned instantly.

**Request:** `multipart/form-data` with a `file` field (JPEG image)

**Response:**
```json
{
  "caption": "I see: A person walking down a sidewalk next to a street with cars parked along the curb.",
  "cached": false
}
```

**Typical latency:** 5–15s (first call), instant on cache hit

---

## Technical Details

### Thread Pool Architecture

```
┌─────────────────────────────────────────┐
│              FastAPI (async)             │
├────────────────────┬────────────────────┤
│  YOLO Executor     │  Florence Executor │
│  (2 threads)       │  (1 thread)        │
│  ~100ms/call       │  ~10s/call         │
│                    │                    │
│  Handles /api/tell │  Handles /api/more │
└────────────────────┴────────────────────┘
```

YOLO and Florence run in **isolated thread pools** so that a slow Florence caption never blocks real-time YOLO detection. This ensures the tap-for-detection path stays responsive even while a scene description is being generated.

### Scene-Change Detection

Before running Florence-2 (which is computationally expensive), the server compares the current frame against the previous one using **Mean Squared Error (MSE)** on downscaled 64x64 grayscale thumbnails. If MSE < 1500, the scene hasn't changed enough to justify re-running inference, and the cached caption is returned instantly.

### CPU-Only Deployment (Flash Attention Workaround)

Florence-2's model file on HuggingFace imports `flash_attn`, which requires CUDA to compile. Since free-tier HF Spaces run on CPU only, the Dockerfile creates a **stub `flash_attn` package** to satisfy the import scanner, and the model is loaded with `attn_implementation="eager"` to use standard PyTorch attention instead. This is transparent to the end user — the model produces identical outputs.

---

## Built With

- [FastAPI](https://fastapi.tiangolo.com/) — async Python web framework
- [ONNX Runtime](https://onnxruntime.ai/) — cross-platform ML inference engine
- [YOLOv26](https://github.com/THU-MIG/yolov10) — real-time object detection
- [Florence-2](https://huggingface.co/microsoft/Florence-2-large) — vision-language model (Microsoft)
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis) — browser-native text-to-speech

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Built by [odd-squad-eye](https://github.com/odd-squad-eye)**

</div>
