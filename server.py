from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import cv2
from PIL import Image
import io
import traceback
import logging

from onnx_detector import detect_image
from florence_server import generate_caption, load_model

# configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("EYE")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# isolated thread pools so heavy Florence inference never starves real-time YOLO detections
yolo_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="yolo")
florence_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="florence")

FLORENCE_TIMEOUT = 45.0

# simple module-level cache for the last Florence result
last_florence_cv2 = None
cached_florence_caption = ""


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(florence_executor, load_model)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


def get_direction(x1, x2, img_width=640):
    center = (x1 + x2) / 2
    third = img_width / 3
    if center < third:
        return "on your left"
    elif center > third * 2:
        return "on your right"
    else:
        return "in front of you"


def get_distance(x1, y1, x2, y2):
    width = x2 - x1
    height = y2 - y1
    area = width * height
    if area > 80000:
        return "very close"
    elif area > 30000:
        return "nearby"
    else:
        return ""


def build_summary(detections):
    if not detections:
        return "The path looks clear."
    
    parts = []
    for det in detections:
        label = det["label"]
        x1, y1, x2, y2 = det["box"]
        direction = get_direction(x1, x2)
        distance = get_distance(x1, y1, x2, y2)
        
        if distance:
            parts.append(f"a {label} {distance} {direction}")
        else:
            parts.append(f"a {label} {direction}")

    if len(parts) == 1:
        return f"I see {parts[0]}."
    elif len(parts) == 2:
        return f"I see {parts[0]} and {parts[1]}."
    else:
        return f"I see {', '.join(parts[:-1])}, and {parts[-1]}."


def calculate_mse(img1, img2):
    """Calculates Mean Squared Error between two images (runs inside a thread pool)."""
    if img1 is None or img2 is None:
        return float('inf')
    
    # resize to 64x64 and convert to grayscale for faster math
    i1 = cv2.resize(cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY), (64, 64))
    i2 = cv2.resize(cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY), (64, 64))
    
    err = np.sum((i1.astype("float") - i2.astype("float")) ** 2)
    err /= float(i1.shape[0] * i1.shape[1])
    return err


async def read_upload(file: UploadFile):
    raw_bytes = await file.read()
    nparr = np.frombuffer(raw_bytes, np.uint8)
    cv2_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return raw_bytes, cv2_frame


@app.post("/api/tell")
async def api_tell(file: UploadFile = File(...)):
    """Captures one frame, runs YOLO, returns a spoken summary."""
    try:
        raw_bytes, cv2_frame = await read_upload(file)

        if cv2_frame is None:
            return JSONResponse({"error": "Invalid image"}, status_code=400)

        loop = asyncio.get_event_loop()
        detections = await loop.run_in_executor(yolo_executor, detect_image, raw_bytes)

        summary = build_summary(detections)
        logger.info(f"YOLO tell: {summary}")

        return {"summary": summary}

    except Exception as e:
        logger.error(f"/api/tell error: {e}")
        traceback.print_exc()
        return JSONResponse({"error": "Detection failed"}, status_code=500)


@app.post("/api/more")
async def api_more(file: UploadFile = File(...)):
    """Captures one frame, runs Florence-2, returns a detailed caption."""
    global last_florence_cv2, cached_florence_caption

    try:
        raw_bytes, cv2_frame = await read_upload(file)

        if cv2_frame is None:
            return JSONResponse({"error": "Invalid image"}, status_code=400)

        loop = asyncio.get_event_loop()

        # check MSE for scene change to reuse cached caption
        mse = await loop.run_in_executor(
            yolo_executor, calculate_mse, cv2_frame, last_florence_cv2
        )
        logger.info(f"Scene MSE: {mse:.1f}")

        if mse < 1500 and cached_florence_caption:
            logger.info("Scene unchanged (MSE < 1500). Returning cache instantly.")
            return {"caption": cached_florence_caption, "cached": True}

        logger.info("Scene changed. Running Florence in isolated thread pool...")
        image = Image.open(io.BytesIO(raw_bytes))

        caption = await asyncio.wait_for(
            loop.run_in_executor(florence_executor, generate_caption, image),
            timeout=FLORENCE_TIMEOUT
        )

        last_florence_cv2 = cv2_frame
        cached_florence_caption = caption

        logger.info("Florence caption delivered successfully")
        return {"caption": caption, "cached": False}

    except asyncio.TimeoutError:
        logger.warning(f"Florence timed out after {FLORENCE_TIMEOUT}s")
        return JSONResponse(
            {"error": "Scene description took too long. Please try again."},
            status_code=504
        )
    except Exception as e:
        logger.error(f"/api/more error: {e}")
        traceback.print_exc()
        return JSONResponse({"error": "Description failed"}, status_code=500)