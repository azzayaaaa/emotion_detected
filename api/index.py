from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse


HOME_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Emotion Lens</title>
    <style>
      :root {
        color-scheme: dark;
        font-family: Arial, Helvetica, sans-serif;
        background: #101318;
        color: #f4f7fb;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background:
          radial-gradient(circle at 20% 20%, rgba(56, 189, 248, 0.18), transparent 30%),
          linear-gradient(135deg, #101318 0%, #18202a 55%, #12161d 100%);
      }

      main {
        width: min(760px, calc(100% - 40px));
        padding: 48px 0;
      }

      h1 {
        margin: 0 0 16px;
        font-size: clamp(40px, 7vw, 72px);
        line-height: 1;
        letter-spacing: 0;
      }

      p {
        max-width: 620px;
        margin: 0 0 28px;
        color: #cbd5e1;
        font-size: 18px;
        line-height: 1.65;
      }

      .actions {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 14px;
      }

      button {
        min-height: 52px;
        border: 0;
        border-radius: 8px;
        padding: 0 22px;
        background: #38bdf8;
        color: #061019;
        cursor: pointer;
        font: 700 16px/1 Arial, Helvetica, sans-serif;
      }

      button:hover {
        background: #7dd3fc;
      }

      .status {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        min-height: 52px;
        padding: 0 14px;
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-radius: 8px;
        background: rgba(15, 23, 42, 0.48);
        color: #e2e8f0;
        font-size: 15px;
      }

      .dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: #22c55e;
        box-shadow: 0 0 18px rgba(34, 197, 94, 0.72);
        flex: 0 0 auto;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>Emotion Lens</h1>
      <p>
        Open the camera in a new tab and detect facial expressions directly in
        the browser.
      </p>
      <div class="actions">
        <button type="button" onclick="window.open('/camera', '_blank', 'noopener')">
          Open Camera
        </button>
        <div class="status">
          <span class="dot" aria-hidden="true"></span>
          Vercel deployment is ready
        </div>
      </div>
    </main>
  </body>
</html>"""


CAMERA_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Emotion Lens Camera</title>
    <style>
      :root {
        color-scheme: dark;
        font-family: Arial, Helvetica, sans-serif;
        background: #090d12;
        color: #f8fafc;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        background: #090d12;
      }

      header {
        min-height: 72px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        padding: 18px 24px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.18);
      }

      h1 {
        margin: 0;
        font-size: 22px;
        letter-spacing: 0;
      }

      #status {
        color: #cbd5e1;
        font-size: 14px;
        text-align: right;
      }

      main {
        min-height: calc(100vh - 72px);
        display: grid;
        place-items: center;
        padding: 24px;
      }

      .stage {
        position: relative;
        width: min(1120px, 100%);
        aspect-ratio: 16 / 9;
        overflow: hidden;
        border: 1px solid rgba(148, 163, 184, 0.24);
        border-radius: 8px;
        background: #020617;
      }

      video,
      canvas {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      video {
        transform: scaleX(-1);
      }

      .result {
        position: absolute;
        left: 18px;
        bottom: 18px;
        min-width: 180px;
        padding: 14px 16px;
        border: 1px solid rgba(148, 163, 184, 0.24);
        border-radius: 8px;
        background: rgba(2, 6, 23, 0.72);
        backdrop-filter: blur(10px);
      }

      .label {
        color: #94a3b8;
        font-size: 12px;
        text-transform: uppercase;
      }

      #emotion {
        margin-top: 4px;
        font-size: 30px;
        font-weight: 800;
        line-height: 1.1;
      }
    </style>
  </head>
  <body>
    <header>
      <h1>Emotion Lens Camera</h1>
      <div id="status">Loading emotion model...</div>
    </header>
    <main>
      <section class="stage">
        <video id="video" autoplay muted playsinline></video>
        <canvas id="overlay"></canvas>
        <div class="result">
          <div class="label">Detected emotion</div>
          <div id="emotion">Waiting</div>
        </div>
      </section>
    </main>

    <script src="https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js"></script>
    <script>
      const MODEL_URL = "https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights";
      const video = document.getElementById("video");
      const canvas = document.getElementById("overlay");
      const statusEl = document.getElementById("status");
      const emotionEl = document.getElementById("emotion");
      const niceNames = {
        angry: "Angry",
        disgusted: "Disgusted",
        fearful: "Fearful",
        happy: "Happy",
        neutral: "Neutral",
        sad: "Sad",
        surprised: "Surprised"
      };

      async function start() {
        try {
          await Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
            faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL)
          ]);

          statusEl.textContent = "Requesting camera permission...";
          const stream = await navigator.mediaDevices.getUserMedia({
            video: {
              facingMode: "user",
              width: { ideal: 1280 },
              height: { ideal: 720 }
            },
            audio: false
          });

          video.srcObject = stream;
          await video.play();
          statusEl.textContent = "Camera running";
          detectLoop();
        } catch (error) {
          statusEl.textContent = "Camera or model failed to start";
          emotionEl.textContent = "Blocked";
          console.error(error);
        }
      }

      async function detectLoop() {
        const displaySize = {
          width: video.videoWidth,
          height: video.videoHeight
        };

        canvas.width = displaySize.width;
        canvas.height = displaySize.height;

        const context = canvas.getContext("2d");

        async function frame() {
          const detection = await faceapi
            .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
            .withFaceExpressions();

          context.clearRect(0, 0, canvas.width, canvas.height);

          if (detection) {
            const resized = faceapi.resizeResults(detection, displaySize);
            const box = resized.detection.box;
            const expressions = resized.expressions;
            const emotion = Object.entries(expressions).sort((a, b) => b[1] - a[1])[0][0];

            emotionEl.textContent = niceNames[emotion] || emotion;
            context.strokeStyle = "#22c55e";
            context.lineWidth = 4;
            context.strokeRect(
              canvas.width - box.x - box.width,
              box.y,
              box.width,
              box.height
            );
          } else {
            emotionEl.textContent = "No face";
          }

          window.requestAnimationFrame(frame);
        }

        frame();
      }

      start();
    </script>
  </body>
</html>"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        html = CAMERA_HTML if path == "/camera" else HOME_HTML

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))
