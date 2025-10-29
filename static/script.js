const video = document.getElementById("webcam");
const canvas = document.getElementById("canvas");
const detectBtn = document.getElementById("detectBtn");
const resultsDiv = document.getElementById("results");

const ctx = canvas.getContext("2d");
let speaking = false;
let detecting = false;

// Start webcam
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    video.srcObject = stream;
    video.addEventListener('loadedmetadata', () => {
      canvas.width = 320;
      canvas.height = 240;
      updateCanvas();
    });
  })
  .catch(err => console.error("Webcam error:", err));

// Continuously draw video frame to canvas
function updateCanvas() {
  if (video.videoWidth && video.videoHeight) {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  }
  requestAnimationFrame(updateCanvas);
}

// Simple beep
function playBeep() {
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const oscillator = audioCtx.createOscillator();
  const gainNode = audioCtx.createGain();
  oscillator.connect(gainNode);
  gainNode.connect(audioCtx.destination);
  oscillator.type = "sine";
  oscillator.frequency.value = 800;
  gainNode.gain.value = 0.1;
  oscillator.start();
  setTimeout(() => {
    oscillator.stop();
    audioCtx.close();
  }, 250);
}

// Object detection
async function detectObjects() {
  if (detecting) return; // Prevent overlapping detection
  detecting = true;

  // Pause recognition while detecting
  if (recognitionActive) recognition.stop();

  // Draw latest frame
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", 0.7));
  const formData = new FormData();
  formData.append("file", blob, "frame.jpg");

  try {
    const response = await fetch("/detect", { method: "POST", body: formData });
    const data = await response.json();

    const objects = data.objects || [];
    const boxes = data.boxes || [];
    let message = "";

    if (objects.length) {
      message = "Detected objects: " + objects.join(", ");
      const closeObjects = [];

      boxes.forEach((box, i) => {
        const [x1, y1, x2, y2] = box.map(Number);
        const widthRatio = (x2 - x1) / video.videoWidth;
        const heightRatio = (y2 - y1) / video.videoHeight;
        if (widthRatio > 0.42 || heightRatio > 0.48) {
          const name = objects[i] ?? "unknown";
          closeObjects.push(name);
        }
      });

      if (closeObjects.length > 0) {
        message += `. Warning! ${closeObjects.join(", ")} too close!`;
        playBeep();
      }
    } else {
      message = "No objects detected.";
    }

    resultsDiv.innerText = message;

    // Speak results
    speaking = true;
    const utterance = new SpeechSynthesisUtterance(message);
    utterance.onend = () => {
      speaking = false;
      if (!recognitionActive) recognition.start(); // Resume recognition
    };
    speechSynthesis.speak(utterance);

  } catch (err) {
    resultsDiv.innerText = "Error detecting objects.";
    console.error(err);
  } finally {
    detecting = false;
  }
}

// =====================
// Button trigger
// =====================
detectBtn.addEventListener("click", detectObjects);

// =====================
// Speech recognition trigger
// =====================
let recognitionActive = false;
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.continuous = true;
recognition.lang = "en-US";

recognition.onstart = () => { recognitionActive = true; };
recognition.onend = () => {
  recognitionActive = false;
  if (!speaking && !detecting) recognition.start(); // auto-restart
};
recognition.onerror = e => {
  console.error("Speech recognition error:", e.error);
  setTimeout(() => recognition.start(), 1000);
};

recognition.onresult = e => {
  const text = e.results[e.results.length - 1][0].transcript.toLowerCase();
  console.log("Heard:", text);
  if (text.includes("ok") && !detecting) { // Trigger detection when user says "okay"
    detectObjects();
  }
};

// Start listening
recognition.start();