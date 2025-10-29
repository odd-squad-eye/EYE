from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ultralytics import YOLO
from PIL import Image
from pathlib import Path
import io

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

model_path = "weight/best.pt"
model = YOLO(model_path)

# new: Serve index.html at "/"
@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# detect endpoint
@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    image_d = await file.read()
    image = Image.open(io.BytesIO(image_d))

    res = model(image)
    d_obj = []
    boxes = []

    for result in res:
        if result.boxes is not None:
            for box in result.boxes:
                cls_id = int(box.cls)
                label = model.names[cls_id]
                d_obj.append(label)

                # Get box coordinates as a list [x1, y1, x2, y2]
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                boxes.append([x1, y1, x2, y2])


    d_obj = list(set(d_obj))
    return JSONResponse({"objects": d_obj, "boxes": boxes})