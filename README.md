---
title: EYE - AI Vision Assistant
colorFrom: gray
colorTo: gray
sdk: docker
app_port: 7860
---

<div align="center">

# 👁️ EYE — AI Vision Assistant

**See the world through sound.**

An AI-powered assistive tool that turns your phone camera into a real-time audio narrator — built for visually impaired users, usable by anyone.

[![Live Demo](https://img.shields.io/badge/🤗_Live_Demo-Hugging_Face-yellow?style=for-the-badge)](https://huggingface.co/spaces/sudo-raj-1/final_eye)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-green?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

</div>

---

## 🎯 What is EYE?

EYE is a **gesture-controlled AI assistant** that uses your phone's camera to describe the world around you — entirely through audio. No visual UI, no buttons to find, no screen to read.

- **Tap once** → instant object detection ("I see a person nearby on your left")
- **Tap twice** → rich scene description ("A person standing in a park with trees and a bench")
- **Works anywhere** — noisy streets, quiet rooms, indoors or outdoors

> **Why gestures instead of voice commands?** Voice recognition fails in noisy environments — the exact places where a visually impaired user needs assistance most. Simple touch gestures work 100% of the time, everywhere.

---

## 🧠 How It Works

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Phone Camera │────▶│  Tap Screen  │────▶│  Capture 1 Frame │────▶│  REST API    │
└─────────────┘     └──────────────┘     └──────────────────┘     │  /api/tell   │
                                                                   │  /api/more   │
                                                                   └──────┬───────┘
                                                                          │
                                                          ┌───────────────┴───────────────┐
                                                          │                               │
                                                    ┌─────▼─────┐                 ┌───────▼───────┐
                                                    │  YOLOv10-X │                 │ Florence-2-L  │
                                                    │  (10ms)    │                 │ (3-10s)       │
                                                    └─────┬─────┘                 └───────┬───────┘
                                                          │                               │
                                                          ▼                               ▼
                                                   "I see a person             "A woman walking her
                                                    nearby on your              dog along a tree-lined
                                                    left."                      sidewalk in the evening."
                                                          │                               │
                                                          └───────────┬───────────────────┘
                                                                      ▼
                                                              🔊 Text-to-Speech
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **REST, not WebSockets** | Simpler, more reliable — no persistent connection to manage or reconnect |
| **Touch gestures, not voice** | Works in noisy environments where voice recognition fails |
| **No camera streaming** | Camera stays local; only sends a single frame when you tap (privacy + bandwidth) |
| **Black screen UI** | No visual elements to distract — the entire interface is audio |
| **Scene caching** | If the scene hasn't changed (MSE < 1500), returns cached description instantly |

---

## 🎮 Controls

### On Phone (Primary)

| Gesture | What Happens |
|---------|-------------|
| **Tap** | Quick scan — YOLO detects objects, tells you what's around |
| **Double tap** | Deep look — Florence-2 describes the full scene in detail |
| **Two-finger tap** | Mute the AI for 5 seconds |
| **Long press** (600ms) | Repeat the last thing it said |

### On Desktop (Testing / Development)

| Input | What Happens |
|-------|-------------|
| **Click** | Quick scan (same as tap) |
| **Double click** | Deep look (same as double tap) |
| **Right-click** | Mute for 5 seconds |
| **Middle-click** | Repeat last |

---

## 🤖 AI Models

| Model | Params | Size | Speed (CPU) | Purpose |
|-------|--------|------|-------------|---------|
| [**YOLOv10-X**](https://github.com/THU-MIG/yolov10) | 56M | 223 MB | ~50-200ms | Object detection with spatial awareness (direction + distance) |
| [**Florence-2-large**](https://huggingface.co/microsoft/Florence-2-large) | 770M | ~1.5 GB | ~5-15s | Rich, natural-language scene captioning |

### Why Two Models?

**YOLO** is fast but shallow — it tells you *what* objects exist and *where* they are. **Florence-2** is slow but deep — it understands the *scene* and describes it like a human would. Together, they give you instant awareness (tap) and detailed understanding (double tap) when you need it.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- A webcam or phone camera
- ~2 GB disk space (for model downloads)

### Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/odd-squad-eye/EYE.git
cd EYE
git checkout proto-2

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
python server.py

# 4. Open in your browser
#    Laptop:  http://localhost:8000
#    Phone:   http://<your-laptop-ip>:8000  (same Wi-Fi network)
```

> **📱 Phone tip:** Open the URL in Chrome/Safari, tap "Start", and allow camera + microphone permissions. The screen will go black — that's intentional. Just start tapping!

### Deploy to Hugging Face Spaces

1. Create a new Space → select **Docker** as the SDK
2. Push this repo (the `Dockerfile` handles everything)
3. YOLO model is included in the repo; Florence-2 downloads automatically on first launch

---

## 📂 Project Structure

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
├── yolo26n.onnx           # YOLOv10 nano model (10 MB, fallback)
├── yolo26x.onnx           # YOLOv10 X model (223 MB, primary)
├── Dockerfile             # Production container (Python 3.11-slim + flash_attn stub)
├── requirements.txt       # Python dependencies
└── LICENSE                # MIT
```

---

## 🔌 API Reference

### `POST /api/tell`

Fast object detection with spatial context.

**Request:** `multipart/form-data` with a `file` field (JPEG image)

**Response:**
```json
{
  "summary": "I see a person very close in front of you and a car nearby on your left."
}
```

**Latency:** ~50–200ms on CPU

---

### `POST /api/more`

Detailed scene captioning using Florence-2. Includes scene-change caching — if the scene hasn't changed significantly, returns the cached result instantly.

**Request:** `multipart/form-data` with a `file` field (JPEG image)

**Response:**
```json
{
  "caption": "I see: A person walking down a sidewalk next to a street with cars parked along the curb.",
  "cached": false
}
```

**Latency:** ~5–15s first call, instant if scene unchanged

---

## ⚙️ Technical Details

### Thread Pool Architecture

```
┌─────────────────────────────────────────┐
│              FastAPI (async)             │
├────────────────────┬────────────────────┤
│  YOLO Executor     │  Florence Executor │
│  (2 threads)       │  (1 thread)        │
│  ~50ms/inference   │  ~10s/inference    │
│                    │                    │
│  Handles /api/tell │  Handles /api/more │
└────────────────────┴────────────────────┘
```

YOLO and Florence run in **isolated thread pools** so that a slow Florence caption never blocks fast YOLO detection. This ensures the tap-for-detection path stays responsive even while a scene description is processing.

### Scene-Change Detection

Before running Florence-2 (which is expensive), the server compares the current frame against the last one using **Mean Squared Error (MSE)** on downscaled 64×64 grayscale thumbnails. If MSE < 1500, the scene hasn't changed enough to re-run inference — the cached caption is returned instantly.

### CPU-Only Flash Attention Workaround

Florence-2's HuggingFace model file imports `flash_attn`, which requires CUDA to install. Since free-tier HF Spaces are CPU-only, the Dockerfile creates a **stub `flash_attn` package** to satisfy the import scanner, and the model is loaded with `attn_implementation="eager"` to use standard PyTorch attention instead.

---

## 🛠️ Built With

- **[FastAPI](https://fastapi.tiangolo.com/)** — async Python web framework
- **[ONNX Runtime](https://onnxruntime.ai/)** — cross-platform ML inference
- **[YOLOv10](https://github.com/THU-MIG/yolov10)** — real-time object detection
- **[Florence-2](https://huggingface.co/microsoft/Florence-2-large)** — vision-language model by Microsoft
- **[Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis)** — browser-native text-to-speech

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ by [odd-squad-eye](https://github.com/odd-squad-eye)**

*Making the world more accessible, one tap at a time.*

</div>
