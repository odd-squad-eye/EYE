// ============================
// DOM ELEMENTS
// ============================

const video = document.getElementById("webcam");
const canvas = document.getElementById("canvas");
const startOverlay = document.getElementById("startOverlay");
const ctx = canvas.getContext("2d");

// ============================
// STATE
// ============================

let lastSpokenText = "";
let isSpeaking = false;
let silenceUntil = 0;
let isPageVisible = true;
let isRequestInFlight = false; // Prevent double-taps from flooding the server

// ============================
// SPEECH OUTPUT
// ============================

function speak(message) {
    if (!message) return;
    if (Date.now() < silenceUntil) return;

    speechSynthesis.cancel();
    isSpeaking = true;

    const utterance = new SpeechSynthesisUtterance(message);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => {
        isSpeaking = false;
        lastSpokenText = message;
    };

    utterance.onerror = (e) => {
        console.warn("Speech error:", e.error);
        isSpeaking = false;
    };

    speechSynthesis.speak(utterance);
}

// ============================
// CAPTURE FRAME
// ============================

function captureFrame() {
    return new Promise((resolve) => {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(
            (blob) => resolve(blob),
            "image/jpeg",
            0.8
        );
    });
}

// ============================
// REST API CALLS
// ============================

async function apiTell() {
    if (isRequestInFlight) return;
    isRequestInFlight = true;

    try {
        const blob = await captureFrame();
        if (!blob) { isRequestInFlight = false; return; }

        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        const res = await fetch("/api/tell", { method: "POST", body: formData });
        const data = await res.json();

        if (data.summary) {
            speak(data.summary);
        } else if (data.error) {
            speak(data.error);
        }
    } catch (e) {
        console.error("apiTell error:", e);
        speak("Connection failed.");
    } finally {
        isRequestInFlight = false;
    }
}

async function apiMore() {
    if (isRequestInFlight) return;
    isRequestInFlight = true;

    speak("Looking closer...");

    try {
        const blob = await captureFrame();
        if (!blob) { isRequestInFlight = false; return; }

        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        const res = await fetch("/api/more", { method: "POST", body: formData });
        const data = await res.json();

        if (data.caption) {
            speak(data.caption);
        } else if (data.error) {
            speak(data.error);
        }
    } catch (e) {
        console.error("apiMore error:", e);
        speak("Connection failed.");
    } finally {
        isRequestInFlight = false;
    }
}

// ============================
// GESTURE SYSTEM
// ============================
// Single tap    → Tell (YOLO summary)
// Double tap    → More (Florence description)
// Two-finger    → Shut (silence AI for 5s)
// Long press    → Repeat last spoken text

let tapTimer = null;
let longPressTimer = null;
let isLongPress = false;
const DOUBLE_TAP_DELAY = 300; // ms window to detect double tap

function setupGestures(target) {
    // --- Prevent default context menus and text selection ---
    target.addEventListener("contextmenu", (e) => e.preventDefault());

    // ---- TOUCH GESTURES (Mobile) ----
    target.addEventListener("touchstart", (e) => {
        // Two-finger tap → Shut
        if (e.touches.length >= 2) {
            e.preventDefault();
            clearTimeout(tapTimer);
            clearTimeout(longPressTimer);
            cmdShut();
            return;
        }

        // Start long-press detection
        isLongPress = false;
        longPressTimer = setTimeout(() => {
            isLongPress = true;
            cmdRepeat();
        }, 600); // 600ms = long press
    }, { passive: false });

    target.addEventListener("touchend", (e) => {
        clearTimeout(longPressTimer);

        // Ignore if it was a long press or multi-finger
        if (isLongPress || e.changedTouches.length > 1) return;
        e.preventDefault();

        // Tap detection with double-tap window
        if (tapTimer) {
            // Second tap within window → Double tap
            clearTimeout(tapTimer);
            tapTimer = null;
            cmdMore();
        } else {
            // First tap — wait to see if a second comes
            tapTimer = setTimeout(() => {
                tapTimer = null;
                cmdTell();
            }, DOUBLE_TAP_DELAY);
        }
    });

    target.addEventListener("touchmove", () => {
        // Cancel long press if finger moves
        clearTimeout(longPressTimer);
    });

    // ---- MOUSE GESTURES (Desktop fallback) ----
    target.addEventListener("click", (e) => {
        // Use similar double-click detection as touch
        if (tapTimer) {
            clearTimeout(tapTimer);
            tapTimer = null;
            cmdMore();
        } else {
            tapTimer = setTimeout(() => {
                tapTimer = null;
                cmdTell();
            }, DOUBLE_TAP_DELAY);
        }
    });

    // Right-click → Shut (desktop equivalent of two-finger tap)
    target.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        cmdShut();
    });

    // Middle click → Repeat (desktop equivalent of long press)
    target.addEventListener("mousedown", (e) => {
        if (e.button === 1) { // Middle mouse button
            e.preventDefault();
            cmdRepeat();
        }
    });
}

// ============================
// COMMANDS
// ============================

function cmdTell() {
    console.log("CMD: tell (single tap)");
    apiTell();
}

function cmdMore() {
    console.log("CMD: more (double tap)");
    apiMore();
}

function cmdShut() {
    console.log("CMD: shut (two-finger / right-click)");
    speechSynthesis.cancel();
    isSpeaking = false;
    silenceUntil = Date.now() + 5000;
}

function cmdRepeat() {
    console.log("CMD: repeat (long press / middle click)");
    if (lastSpokenText) {
        speak(lastSpokenText);
    } else {
        speak("Nothing to repeat yet.");
    }
}

// ============================
// PAGE VISIBILITY API
// ============================

document.addEventListener("visibilitychange", () => {
    isPageVisible = !document.hidden;

    if (!isPageVisible) {
        console.log("Page hidden — silencing speech");
        speechSynthesis.cancel();
        isSpeaking = false;
    }
});

// ============================
// CAMERA INIT
// ============================

function initCamera() {
    // Try rear camera first (mobile), fall back to any camera (laptop)
    navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } }
    })
    .then(onCameraReady)
    .catch(() => {
        console.log("Rear camera not available, trying any camera...");
        return navigator.mediaDevices.getUserMedia({ video: true });
    })
    .then(onCameraReady)
    .catch((err) => {
        console.error("Camera error:", err);
        speak("Camera access failed. Please allow camera permissions.");
    });
}

function onCameraReady(stream) {
    if (!stream || video.srcObject) return; // Prevent double-init
    video.srcObject = stream;
    video.addEventListener("loadedmetadata", () => {
        canvas.width = 640;
        canvas.height = 480;
        speak("System online. Tap the screen to hear what I see.");
    });
}

// ============================
// CLICK TO START
// ============================

startOverlay.addEventListener("click", () => {
    startOverlay.classList.add("hidden");
    initCamera();

    // Set up gesture listeners on the body (full-screen black tap target)
    setupGestures(document.body);
});