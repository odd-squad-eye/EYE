<div align="center">

# 👁️ EYE (Prototype-1)

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Model Core](https://img.shields.io/badge/Engine-YOLO11%20(Ultralytics)-orange?style=for-the-badge&logo=computervision)](https://github.com/ultralytics/ultralytics)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Branch: Proto-1](https://img.shields.io/badge/Branch-proto--1-red?style=for-the-badge&logo=git)](https://github.com/odd-squad-eye/EYE/tree/proto-1)

**The core inference, tracking, and deep learning intelligence engine for the Odd Squad ecosystem.**

[Explore Features](#-key-features) • [System Architecture](#-architectural-ecosystem) • [Quick Start](#-quick-start) • [Configuration](#%EF%B8%8F-configuration)

</div>

---

## 📖 Overview

**EYE** serves as the central brain for our multi-component computer vision pipeline. Built upon the state-of-the-art **YOLO11** framework, this project handles raw visual inputs to execute ultra-fast, real-time object detection, object instance segmentation, and predictive spatial tracking. 

This specific branch (`proto-1`) contains the baseline prototype structure, modularizing our deep learning workflows to provide stability, edge-device friendliness, and reliable data throughput.

---

## 🛰️ Architectural Ecosystem

The **Odd Squad** vision system isolates ingestion from computation for maximum throughput and low-latency execution:

              ┌──────────────────────────────┐
              │          RETINA              │  <- (Visual Input Layer)
              │  (Camera / Frame Ingestion)  │
              └──────────────┬───────────────┘
                             │
               [ Raw Video / Frame Stream ]
                             │
                             ▼
              ┌──────────────────────────────┐
              │             EYE              │  <- (Inference Core)
              │   - YOLO11 Tracking          │
              │   - Object Segmentation      │
              │   - Deep Learning Analytics  │
              └──────────────────────────────┘

* **[retina](https://github.com/odd-squad-eye/retina):** The optical capturing component. Manages physical lenses, RTSP streams, and raw video frame buffering.
* **[EYE](https://github.com/odd-squad-eye/EYE):** This repository. It takes the buffered streams, applies the custom weights, processes mathematical spatial coordinates, and exposes target bounding maps.

---

## ⚡ Key Features

* **YOLO11 Native Integration:** Leverages the latest improvements in attention mechanics and backbone optimizations from the Ultralytics lineup.
* **Dual Mode Execution:** Seamlessly switches between high-speed standard **Object Detection** bounding boxes and pixel-perfect **Instance Segmentation**.
* **Modular Callbacks:** Pre-built triggers designed to pass real-time JSON or matrix data outputs to adjacent components.
* **Hardware Accelerated:** Out-of-the-box support for CUDA, Apple Silicon (MPS), and fallback CPU optimization routines.

---

## 🚀 Quick Start

Ensure you have Python 3.9+ and standard virtualization tools installed.

### 1. Clone the Prototype Branch
```bash
git clone -b proto-1 [https://github.com/odd-squad-eye/EYE.git](https://github.com/odd-squad-eye/EYE.git)
cd EYE
2. Set Up Environment
# Create a virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
3. Install Dependencies
pip install --upgrade pip
pip install -r requirements.txt
🛠️ Configuration & Basic Usage
```
You can initialize model inferences programmatically or run baseline test files directly:

Basic Python Quickstart
Python
```
from ultralytics import YOLO

# Load the local prototype-1 weights configuration
model = YOLO("yolo11n.pt")  # or specify your custom configured weights file
 # Run inference on an image or stream path
results = model.predict(source="data/sample.mp4", show=True, save=True)

for result in results:
    boxes = result.boxes  # Bounding box object outputs
    masks = result.masks  # Segmentation mask outputs
```
Running Test Inference script
```
python run_inference.py --source data/test_input.mp4 --weights yolo11n.pt
```
🗺️ Roadmap & Proto-1 Deliverables
[x] Initial YOLO11 network backbone implementation.

[x] Stream pipeline processing framework.

[ ] Integration hooks for the retina hardware streaming companion repo.

[ ] Deployment configurations for edge nodes (TensorRT / ONNX exports).

📄 License
This project is licensed under the MIT License — see the LICENSE file for complete details.
