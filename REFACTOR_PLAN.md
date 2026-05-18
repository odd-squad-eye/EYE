# Architecture Refactor: From WebSocket/Voice to REST/Gestures

This document outlines the planned architectural shift to massively simplify the EYE assistant codebase while maintaining identical AI capabilities (YOLOv26 and Florence-2).

## The Goal
Reduce code complexity ("exponential complexity") by ~60%, eliminate "silent deaths" caused by browser microphone security, and make the app bulletproof in noisy environments. 

## What STAYS THE SAME (The Good Stuff)
- **The AI Pipeline**: `onnx_detector.py` (YOLO) and `florence_server.py` (Florence-2) remain completely unchanged.
- **The UI/UX**: The screen remains a pitch-black, distraction-free "Jarvis-style" interface.
- **The Voice**: The system will still speak the descriptions out loud using the exact same Text-to-Speech voices.
- **Background Pre-Warming**: Florence will still load into the GPU at startup so it's instantly ready.

## What CHANGES (The De-Bloat)

### 1. Removing Voice Commands (Web Speech API)
**Why:** The microphone API is inherently unstable for 24/7 background listening. It causes silent crashes and doesn't work in crowded areas.
**Replacement:** Invisible Touch Gestures on the black screen.
- **Single Tap**: Replaces "Tell" (Instant YOLO summary).
- **Double Tap**: Replaces "More" (Detailed Florence description).
- **Two-Finger Tap**: Replaces "Shut" (Instantly silences the AI).
- **Long Press**: Replaces "Repeat" (Replays last spoken text).

### 2. Removing WebSockets (Constant Streaming)
**Why:** Sending frames 24/7 requires ping/pongs, exponential backoff reconnects, LIFO queues, and complex state machines. This is where 90% of the bugs live.
**Replacement:** Action-Driven REST Endpoints (HTTP POST).
- The camera runs on your phone but *does not send data* until you tap the screen.
- **When you Single Tap**: The frontend captures *one* frame and sends a simple `POST /api/tell` request. The server replies with text.
- **When you Double Tap**: The frontend captures *one* frame and sends a simple `POST /api/more` request. The server replies with text.

### Step-by-Step Implementation Plan

1. **Backend Cleanup (`server.py`)**:
   - Delete the `websocket_endpoint` completely.
   - Delete the `yolo_loop`, `asyncio.Queue`, and `ConnectionState`.
   - Add two simple FastAPI routes:
     ```python
     @app.post("/api/tell")
     async def api_tell(file: UploadFile): ... # Runs YOLO once
     
     @app.post("/api/more")
     async def api_more(file: UploadFile): ... # Runs Florence once
     ```

2. **Frontend Cleanup (`script.js`)**:
   - Delete `SpeechRecognition` setup, auto-restart loops, and `handleCommand`.
   - Delete WebSocket connection logic, ping intervals, and reconnect timers.
   - Add event listeners for `click` (single tap), `dblclick` (double tap), and `contextmenu` (long press).
   - Wire the taps to fetch data via `fetch('/api/tell', { method: 'POST', body: imageBlob })`.

By executing this plan, we will delete hundreds of lines of brittle networking code and replace it with standard, flawlessly reliable web requests.
