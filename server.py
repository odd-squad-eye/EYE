from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ultralytics import YOLO
from PIL import Image
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

model = YOLO("yolo11x.pt")

# new: Serve index.html at "/"
@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# detect endpoint
@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))

    results = model(image)
    detected_objects = []

    for result in results:
        if result.boxes is not None:
            for cls in result.boxes.cls:
                detected_objects.append(model.names[int(cls)])

    detected_objects = list(set(detected_objects))
    return JSONResponse({"objects": detected_objects})