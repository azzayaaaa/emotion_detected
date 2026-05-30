from http.server import BaseHTTPRequestHandler


HTML = """<!doctype html>
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
        margin: 0 0 24px;
        color: #cbd5e1;
        font-size: 18px;
        line-height: 1.65;
      }

      .status {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
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
        A Python OpenCV emotion detector for local camera, image, and video
        analysis. The desktop app runs locally, while this page confirms the
        project is deployed on Vercel.
      </p>
      <div class="status">
        <span class="dot" aria-hidden="true"></span>
        Vercel deployment is ready
      </div>
    </main>
  </body>
</html>"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))
