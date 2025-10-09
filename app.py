import streamlit as st
import requests
from PIL import Image
import io
import streamlit.components.v1 as components

st.set_page_config(page_title="YOLO Detector", layout="centered")

st.title("YOLO Detector — Streamlit Frontend")
st.write("Upload an image and get detected object classes from the FastAPI backend.")

backend_url = st.text_input("Backend URL", value="http://localhost:8000/detect")

uploaded_file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg"]) 

if uploaded_file is not None:
    image_bytes = uploaded_file.read()
    img = Image.open(io.BytesIO(image_bytes))
    st.image(img, caption="Uploaded image", use_column_width=True)

    if st.button("Detect Objects"):
        with st.spinner("Sending image to backend..."):
            try:
                files = {"file": (uploaded_file.name, image_bytes, uploaded_file.type)}
                resp = requests.post(backend_url, files=files, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                objects = data.get("objects", [])

                if objects:
                    st.success(f"Detected objects: {', '.join(objects)}")
                else:
                    st.info("No objects detected.")
            except Exception as e:
                st.error(f"Error calling backend: {e}")

st.markdown("---")
st.header("Real-time camera (browser)")
st.write("This uses your browser webcam to capture frames and POST them to the backend `/detect` endpoint at regular intervals. It requires that the backend is reachable from your browser (CORS is already enabled in `server.py`).")

live_backend = st.text_input("Backend URL for live camera", value="http://localhost:8000/detect", key="live_backend")

html_template = """
<div>
    <video id="video" width="640" height="480" autoplay playsinline></video>
    <canvas id="canvas" width="640" height="480" style="display:none;"></canvas>
    <div style="margin-top:8px;">
        <button id="start">Start</button>
        <button id="stop">Stop</button>
        &nbsp; Interval (ms): <input id="interval" type="number" value="1000" min="100" step="100" style="width:90px;"/>
    </div>
    <div id="status" style="margin-top:8px;font-weight:600;"></div>
    <div id="labels" style="margin-top:6px;color:#2b6cb0;"></div>
</div>
<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const startBtn = document.getElementById('start');
const stopBtn = document.getElementById('stop');
const status = document.getElementById('status');
const labels = document.getElementById('labels');
let stream, timer;

async function start() {
    labels.innerHTML = '';
    try {
        stream = await navigator.mediaDevices.getUserMedia({video:true});
        video.srcObject = stream;
        const ctx = canvas.getContext('2d');
        const intervalInput = document.getElementById('interval');
        const backend = "__BACKEND_URL__";
        timer = setInterval(async () => {
            if (video.videoWidth === 0 || video.videoHeight === 0) return;
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video,0,0,canvas.width,canvas.height);
            canvas.toBlob(async (blob) => {
                const form = new FormData();
                form.append('file', blob, 'frame.jpg');
                status.innerText = 'Sending...';
                try {
                    const resp = await fetch(backend, {method:'POST', body: form});
                    if (!resp.ok) {
                        status.innerText = 'Error: ' + resp.status + ' ' + resp.statusText;
                        return;
                    }
                    const data = await resp.json();
                    const objs = data.objects || [];
                    labels.innerText = objs.length ? 'Detected: ' + objs.join(', ') : 'No objects';
                    status.innerText = 'OK — last sent: ' + new Date().toLocaleTimeString();
                } catch (err) {
                    status.innerText = 'Fetch error: ' + err;
                }
            }, 'image/jpeg', 0.7);
        }, Number(intervalInput.value));
    } catch (e) {
        status.innerText = 'Camera error: ' + e;
    }
}

function stop() {
    clearInterval(timer);
    if (stream) {
        stream.getTracks().forEach(t=>t.stop());
    }
    status.innerText = 'Stopped';
}

startBtn.onclick = start;
stopBtn.onclick = stop;
</script>
"""

html = html_template.replace('__BACKEND_URL__', live_backend)
components.html(html, height=720)
