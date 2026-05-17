import onnxruntime as ort
import numpy as np
import cv2
import os

# Use nano model (10MB) — fast enough for real-time assistive detection
# Falls back to larger model if nano isn't found
_DIR = os.path.dirname(os.path.abspath(__file__))

if os.path.exists(os.path.join(_DIR, "yolo26n.onnx")):
    MODEL_PATH = os.path.join(_DIR, "yolo26n.onnx")
elif os.path.exists(os.path.join(_DIR, "yolo26x.onnx")):
    MODEL_PATH = os.path.join(_DIR, "yolo26x.onnx")
else:
    raise FileNotFoundError("No YOLO ONNX model found. Place yolo26n.onnx in the project root.")

COCO_CLASSES = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane",
    5: "bus", 6: "train", 7: "truck", 8: "boat", 9: "traffic light",
    10: "fire hydrant", 11: "stop sign", 12: "parking meter", 13: "bench",
    14: "bird", 15: "cat", 16: "dog", 17: "horse", 18: "sheep", 19: "cow",
    20: "elephant", 21: "bear", 22: "zebra", 23: "giraffe", 24: "backpack",
    25: "umbrella", 26: "handbag", 27: "tie", 28: "suitcase", 29: "frisbee",
    30: "skis", 31: "snowboard", 32: "sports ball", 33: "kite",
    34: "baseball bat", 35: "baseball glove", 36: "skateboard", 37: "surfboard",
    38: "tennis racket", 39: "bottle", 40: "wine glass", 41: "cup",
    42: "fork", 43: "knife", 44: "spoon", 45: "bowl", 46: "banana",
    47: "apple", 48: "sandwich", 49: "orange", 50: "broccoli", 51: "carrot",
    52: "hot dog", 53: "pizza", 54: "donut", 55: "cake", 56: "chair",
    57: "couch", 58: "potted plant", 59: "bed", 60: "dining table",
    61: "toilet", 62: "tv", 63: "laptop", 64: "mouse", 65: "remote",
    66: "keyboard", 67: "cell phone", 68: "microwave", 69: "oven",
    70: "toaster", 71: "sink", 72: "refrigerator", 73: "book",
    74: "clock", 75: "vase", 76: "scissors", 77: "teddy bear",
    78: "hair drier", 79: "toothbrush"
}

import multiprocessing

print("Loading ONNX Runtime model...")
options = ort.SessionOptions()
options.intra_op_num_threads = max(1, multiprocessing.cpu_count() // 2)
options.inter_op_num_threads = 1
session = ort.InferenceSession(MODEL_PATH, sess_options=options, providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
print("ONNX model loaded successfully!")

def detect_image(image_input, conf_threshold=0.6):
    if isinstance(image_input, bytes):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif isinstance(image_input, str):
        img = cv2.imread(image_input)
    else:
        return []

    if img is None:
        return []

    orig_h, orig_w = img.shape[:2]
    
    # Letterbox resize to 640x640
    input_size = 640
    scale = min(input_size / orig_w, input_size / orig_h)
    new_w, new_h = int(orig_w * scale), int(orig_h * scale)
    
    resized_img = cv2.resize(img, (new_w, new_h))
    
    # Pad to 640x640
    pad_w = (input_size - new_w) / 2
    pad_h = (input_size - new_h) / 2
    top, bottom = int(round(pad_h - 0.1)), int(round(pad_h + 0.1))
    left, right = int(round(pad_w - 0.1)), int(round(pad_w + 0.1))
    
    padded_img = cv2.copyMakeBorder(resized_img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
    
    # Preprocess for ONNX: BGR -> RGB, HWC -> CHW, 0-255 -> 0.0-1.0
    blob = padded_img[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
    blob = np.expand_dims(blob, axis=0)
    
    # Run Inference
    outputs = session.run(None, {session.get_inputs()[0].name: blob})
    preds = outputs[0][0] # Shape (300, 6)
    
    detections = []
    
    for pred in preds:
        x1, y1, x2, y2, conf, cls_id = pred
        cls_id = int(cls_id)
        
        if conf > conf_threshold:
            # Scale coordinates back to original image size
            x1 = (x1 - pad_w) / scale
            y1 = (y1 - pad_h) / scale
            x2 = (x2 - pad_w) / scale
            y2 = (y2 - pad_h) / scale
            
            label = COCO_CLASSES.get(cls_id, f"class_{cls_id}")
            
            detections.append({
                "class_id": cls_id,
                "label": label,
                "confidence": float(conf),
                "box": [float(x1), float(y1), float(x2), float(y2)]
            })
            
    return detections

if __name__ == "__main__":
    # Warmup
    print("Warming up...")
    detect_image("temp.jpg")
    detect_image("temp.jpg")
    
    import time
    start = time.time()
    res = detect_image("temp.jpg")
    print(f"Time: {(time.time() - start)*1000:.2f} ms")
    print("Detections:", res)
