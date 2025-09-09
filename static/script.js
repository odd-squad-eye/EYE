const video = document.getElementById("webcam");
const canvas = document.getElementById("canvas");
const detectBtn = document.getElementById("detectBtn");
const resultsDiv = document.getElementById("results");

// Start webcam
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    video.srcObject = stream;
  })
  .catch(err => console.error("Webcam error:", err));

detectBtn.addEventListener("click", async () => {
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg"));

  const formData = new FormData();
  formData.append("file", blob, "frame.jpg");

  try {
    const response = await fetch("/detect", { method: "POST", body: formData });
    const data = await response.json();

    if (data.objects && data.objects.length > 0) {
      resultsDiv.innerText = "Detected Objects: " + data.objects.join(", ");
      speechSynthesis.speak(new SpeechSynthesisUtterance(data.objects.join(", ")));
    } else {
      resultsDiv.innerText = "No objects detected.";
    }
  } catch (error) {
    resultsDiv.innerText = "Error detecting objects.";
    console.error("Detection error:", error);
  }
});