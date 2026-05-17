const video = document.getElementById("webcam");
const canvas = document.getElementById("canvas");
const startOverlay = document.getElementById("startOverlay");
const ctx = canvas.getContext("2d");

let lastSpokenText = "";
let isSpeaking = false;
let silenceUntil = 0;
let isPageVisible = true;
let isRequestInFlight = false; // prevents double-taps from flooding the server

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

function captureFrame() {
    return new Promise((resolve) => {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.8);
    });
}

async function apiTell() {
    if (isRequestInFlight) return;
    isRequestInFlight = true;

    try {
        const blob = await captureFrame();
        if (!blob) {
            isRequestInFlight = false;
            return;
        }

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
        if (!blob) {
            isRequestInFlight = false;
            return;
        }

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

// gesture setup
let tapTimer = null;
let longPressTimer = null;
let isLongPress = false;
const DOUBLE_TAP_DELAY = 300; 

function setupGestures(target) {
    // prevent default context menus and text selection
    target.addEventListener("contextmenu", (e) => e.preventDefault());

    // mobile touch gestures
    target.addEventListener("touchstart", (e) => {
        if (e.touches.length >= 2) {
            e.preventDefault();
            clearTimeout(tapTimer);
            clearTimeout(longPressTimer);
            cmdShut();
            return;
        }

        isLongPress = false;
        longPressTimer = setTimeout(() => {
            isLongPress = true;
            cmdRepeat();
        }, 600); 
    }, { passive: false });

    target.addEventListener("touchend", (e) => {
        clearTimeout(longPressTimer);

        if (isLongPress || e.changedTouches.length > 1) return;
        e.preventDefault();

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

    target.addEventListener("touchmove", () => {
        clearTimeout(longPressTimer);
    });

    // desktop mouse gestures fallback
    target.addEventListener("click", (e) => {
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

    target.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        cmdShut();
    });

    target.addEventListener("mousedown", (e) => {
        if (e.button === 1) { 
            e.preventDefault();
            cmdRepeat();
        }
    });
}

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

document.addEventListener("visibilitychange", () => {
    isPageVisible = !document.hidden;

    if (!isPageVisible) {
        console.log("Page hidden — silencing speech");
        speechSynthesis.cancel();
        isSpeaking = false;
    }
});

function initCamera() {
    // try rear camera first (mobile), fall back to any camera (laptop)
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
    if (!stream || video.srcObject) return;
    video.srcObject = stream;
    video.addEventListener("loadedmetadata", () => {
        canvas.width = 640;
        canvas.height = 480;
        speak("System online. Tap the screen to hear what I see.");
    });
}

startOverlay.addEventListener("click", () => {
    startOverlay.classList.add("hidden");
    initCamera();
    setupGestures(document.body);
});