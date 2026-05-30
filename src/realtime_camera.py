from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import cv2


WINDOW_NAME = "Emotion Lens - Real Time"
_DEEPFACE = None
_FACE_CASCADE = None


@dataclass
class LiveFace:
    emotion: str
    confidence: float
    region: dict[str, int]
    scores: dict[str, float]


def main() -> None:
    args = parse_args()
    if args.image:
        run_image(args.image, args.save_dir)
        return
    if args.video:
        run_video(args.video, args.every, args.save_dir)
        return
    if should_show_launcher():
        run_launcher(args)
        return

    run_camera(args.camera, args.every, not args.no_mirror, args.save_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real-time emotion detection from notebook camera.")
    parser.add_argument("--camera", type=int, default=0, help="Camera index. Default: 0")
    parser.add_argument("--every", type=int, default=8, help="Analyze every N frames. Default: 8")
    parser.add_argument("--no-mirror", action="store_true", help="Disable selfie-style camera mirror.")
    parser.add_argument("--image", type=Path, help="Detect emotion from an image file.")
    parser.add_argument("--video", type=Path, help="Detect emotion from a video file.")
    parser.add_argument("--save-dir", type=Path, default=Path("captures"), help="Folder for screenshots.")
    return parser.parse_args()


def should_show_launcher() -> bool:
    direct_flags = {"--camera", "--no-mirror", "--image", "--video"}
    return not any(arg == flag or arg.startswith(f"{flag}=") for arg in sys.argv[1:] for flag in direct_flags)


def run_launcher(args: argparse.Namespace) -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.title("Emotion Lens")
    root.geometry("460x330")
    root.resizable(False, False)
    root.configure(bg="#07110b")

    selected: tuple[str, Path | None] | None = None

    def choose_camera() -> None:
        nonlocal selected
        selected = ("camera", None)
        root.destroy()

    def choose_image() -> None:
        nonlocal selected
        path = filedialog.askopenfilename(
            title="Choose image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if path:
            selected = ("image", Path(path))
            root.destroy()

    def choose_video() -> None:
        nonlocal selected
        path = filedialog.askopenfilename(
            title="Choose video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("All files", "*.*"),
            ],
        )
        if path:
            selected = ("video", Path(path))
            root.destroy()

    def on_close() -> None:
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    frame = tk.Frame(root, bg="#07110b")
    frame.pack(fill="both", expand=True, padx=34, pady=28)

    title = tk.Label(
        frame,
        text="Emotion Lens",
        font=("Segoe UI", 28, "bold"),
        fg="#48ff74",
        bg="#07110b",
    )
    title.pack(anchor="w")

    subtitle = tk.Label(
        frame,
        text="Choose a source to detect emotion.",
        font=("Segoe UI", 11),
        fg="#b8c9bd",
        bg="#07110b",
    )
    subtitle.pack(anchor="w", pady=(4, 24))

    make_button(frame, "Camera", choose_camera).pack(fill="x", pady=7)
    make_button(frame, "Image", choose_image).pack(fill="x", pady=7)
    make_button(frame, "Video", choose_video).pack(fill="x", pady=7)

    root.mainloop()

    if selected is None:
        return

    mode, path = selected
    try:
        if mode == "camera":
            run_camera(args.camera, args.every, not args.no_mirror, args.save_dir)
        elif mode == "image" and path is not None:
            run_image(path, args.save_dir)
        elif mode == "video" and path is not None:
            run_video(path, args.every, args.save_dir)
    except Exception as error:
        messagebox.showerror("Emotion Lens", str(error))


def make_button(parent, text: str, command):
    import tkinter as tk

    return tk.Button(
        parent,
        text=text,
        command=command,
        font=("Segoe UI", 14, "bold"),
        fg="#07110b",
        bg="#48ff74",
        activeforeground="#07110b",
        activebackground="#77ff9b",
        bd=0,
        relief="flat",
        cursor="hand2",
        height=2,
    )


def run_camera(camera_index: int, analyze_every: int, mirror: bool, save_dir: Path) -> None:
    camera = open_camera(camera_index)
    if camera is None:
        raise RuntimeError(f"Camera {camera_index} did not open. Close other camera apps and try again.")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1100, 700)

    last_faces: list[LiveFace] = []
    analyzer = FrameAnalyzer()
    frame_count = 0

    print("Emotion Lens started.")
    print("Controls: Q = quit, S = save screenshot, +/- = analyze speed")

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                break

            if mirror:
                frame = cv2.flip(frame, 1)

            frame_count += 1
            fresh_faces = analyzer.get_latest()
            if fresh_faces is not None:
                last_faces = fresh_faces

            if frame_count % max(1, analyze_every) == 0:
                analyzer.submit(frame)

            display = draw_overlay(frame, last_faces, analyzer.busy)
            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break
            if key in (ord("s"), ord("S")):
                save_screenshot(display, save_dir)
            if key in (ord("+"), ord("=")):
                analyze_every = max(1, analyze_every - 1)
            if key in (ord("-"), ord("_")):
                analyze_every += 1
    finally:
        analyzer.close()
        camera.release()
        cv2.destroyAllWindows()


def run_image(image_path: Path, save_dir: Path) -> None:
    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError(f"Image not found or unsupported: {image_path}")

    resized = resize_for_analysis(image, width=900)
    scale_x = image.shape[1] / resized.shape[1]
    scale_y = image.shape[0] / resized.shape[0]
    faces = [scale_face(face, scale_x, scale_y) for face in analyze_frame(resized)]

    display = draw_overlay(image, faces, analyzing=False)
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.imshow(WINDOW_NAME, display)
    print("Image analyzed. Press S to save, Q/Esc to close.")

    while True:
        key = cv2.waitKey(0) & 0xFF
        if key in (ord("q"), ord("Q"), 27):
            break
        if key in (ord("s"), ord("S")):
            save_screenshot(display, save_dir)
    cv2.destroyAllWindows()


def run_video(video_path: Path, analyze_every: int, save_dir: Path) -> None:
    video = cv2.VideoCapture(str(video_path))
    if not video.isOpened():
        raise RuntimeError(f"Video not found or unsupported: {video_path}")

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    analyzer = FrameAnalyzer()
    last_faces: list[LiveFace] = []
    frame_count = 0

    print("Video mode started. Controls: Q = quit, S = save screenshot, +/- = analyze speed")
    try:
        while True:
            ok, frame = video.read()
            if not ok:
                break

            frame_count += 1
            fresh_faces = analyzer.get_latest()
            if fresh_faces is not None:
                last_faces = fresh_faces
            if frame_count % max(1, analyze_every) == 0:
                analyzer.submit(frame)

            display = draw_overlay(frame, last_faces, analyzer.busy)
            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break
            if key in (ord("s"), ord("S")):
                save_screenshot(display, save_dir)
            if key in (ord("+"), ord("=")):
                analyze_every = max(1, analyze_every - 1)
            if key in (ord("-"), ord("_")):
                analyze_every += 1
    finally:
        analyzer.close()
        video.release()
        cv2.destroyAllWindows()


def open_camera(camera_index: int):
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    for backend in backends:
        camera = cv2.VideoCapture(camera_index, backend)
        if camera.isOpened():
            return camera
        camera.release()
    return None


class FrameAnalyzer:
    def __init__(self) -> None:
        self.busy = False
        self.closed = False
        self.latest_faces: list[LiveFace] | None = None
        self.lock = threading.Lock()

    def submit(self, frame_bgr) -> None:
        with self.lock:
            if self.busy or self.closed:
                return
            self.busy = True

        frame_copy = frame_bgr.copy()
        thread = threading.Thread(target=self._analyze, args=(frame_copy,), daemon=True)
        thread.start()

    def get_latest(self) -> list[LiveFace] | None:
        with self.lock:
            faces = self.latest_faces
            self.latest_faces = None
            return faces

    def close(self) -> None:
        with self.lock:
            self.closed = True

    def _analyze(self, frame_bgr) -> None:
        faces: list[LiveFace] = []
        try:
            resized = resize_for_analysis(frame_bgr, width=640)
            scale_x = frame_bgr.shape[1] / resized.shape[1]
            scale_y = frame_bgr.shape[0] / resized.shape[0]
            faces = analyze_frame(resized)
            faces = [scale_face(face, scale_x, scale_y) for face in faces]
        except Exception as error:
            print(f"Analysis skipped: {error}")
        finally:
            with self.lock:
                self.latest_faces = faces
                self.busy = False


def resize_for_analysis(frame_bgr, width: int):
    h, w = frame_bgr.shape[:2]
    if w <= width:
        return frame_bgr
    ratio = width / w
    return cv2.resize(frame_bgr, (width, int(h * ratio)), interpolation=cv2.INTER_AREA)


def scale_face(face: LiveFace, scale_x: float, scale_y: float) -> LiveFace:
    region = face.region.copy()
    region["x"] = int(region.get("x", 0) * scale_x)
    region["y"] = int(region.get("y", 0) * scale_y)
    region["w"] = int(region.get("w", 0) * scale_x)
    region["h"] = int(region.get("h", 0) * scale_y)
    return LiveFace(face.emotion, face.confidence, region, face.scores)


def analyze_frame(frame_bgr) -> list[LiveFace]:
    try:
        results = get_deepface().analyze(
            img_path=frame_bgr,
            actions=["emotion"],
            detector_backend="opencv",
            enforce_detection=False,
            silent=True,
        )
    except Exception as error:
        print(f"Analysis skipped: {error}")
        return []

    if isinstance(results, dict):
        results = [results]

    faces: list[LiveFace] = []
    for item in results:
        region = parse_region(item.get("region") or {})
        if region["w"] <= 0 or region["h"] <= 0:
            continue

        scores = {
            name: float(score)
            for name, score in sorted(
                (item.get("emotion") or {}).items(),
                key=lambda pair: float(pair[1]),
                reverse=True,
            )
        }
        emotion = str(item.get("dominant_emotion", "neutral")).lower()
        faces.append(
            LiveFace(
                emotion=emotion,
                confidence=scores.get(emotion, 0.0),
                region=region,
                scores=scores,
            )
        )

    return faces


def parse_region(region: dict) -> dict[str, int]:
    return {
        "x": safe_int(region.get("x")),
        "y": safe_int(region.get("y")),
        "w": safe_int(region.get("w")),
        "h": safe_int(region.get("h")),
    }


def safe_int(value, default: int = 0) -> int:
    if value is None or isinstance(value, (tuple, list, dict)):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_deepface():
    global _DEEPFACE
    if _DEEPFACE is None:
        from deepface import DeepFace

        _DEEPFACE = DeepFace
    return _DEEPFACE


def draw_overlay(frame_bgr, faces: list[LiveFace], analyzing: bool):
    canvas = frame_bgr.copy()
    quick_faces = detect_faces_fast(frame_bgr)

    if faces:
        for index, face in enumerate(faces):
            if index < len(quick_faces):
                x, y, w, h = quick_faces[index]
            else:
                x = max(0, face.region.get("x", 0))
                y = max(0, face.region.get("y", 0))
                w = max(1, face.region.get("w", 1))
                h = max(1, face.region.get("h", 1))
            draw_face_card(canvas, x, y, w, h, face.emotion.title())
    else:
        for x, y, w, h in quick_faces:
            draw_face_box(canvas, x, y, w, h)

    return canvas


def draw_face_card(canvas, x: int, y: int, w: int, h: int, label: str) -> None:
    draw_face_box(canvas, x, y, w, h)

    dark_green = (18, 118, 52)
    shadow = (10, 20, 14)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.78
    thickness = 2
    text_size, _ = cv2.getTextSize(label, font, font_scale, thickness)
    label_w = max(w, text_size[0] + 28)
    label_h = 38
    label_y1 = max(0, y - label_h)

    cv2.rectangle(canvas, (x + 3, label_y1 + 3), (x + label_w + 3, y + 3), shadow, -1)
    cv2.rectangle(canvas, (x, label_y1), (x + label_w, y), dark_green, -1)
    cv2.putText(canvas, label, (x + 14, max(25, y - 11)), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)


def draw_face_box(canvas, x: int, y: int, w: int, h: int) -> None:
    green = (72, 255, 116)
    shadow = (10, 20, 14)

    cv2.rectangle(canvas, (x + 4, y + 4), (x + w + 4, y + h + 4), shadow, 3)
    cv2.rectangle(canvas, (x, y), (x + w, y + h), green, 3)


def detect_faces_fast(frame_bgr) -> list[tuple[int, int, int, int]]:
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _FACE_CASCADE = cv2.CascadeClassifier(cascade_path)

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(70, 70))
    return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]


def save_screenshot(frame, save_dir: Path) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = save_dir / f"emotion_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
    cv2.imwrite(str(filename), frame)
    print(f"Saved screenshot: {filename}")
