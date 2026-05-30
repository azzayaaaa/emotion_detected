# Emotion Lens

Python OpenCV emotion detector. It can use your notebook camera, an image file, or a video file. The window stays clean: no FPS text, no top bar, just green face boxes and the emotion label.

## Folder Structure

```text
emotion/
|-- app.py
|-- run.bat
|-- requirements.txt
|-- README.md
`-- src/
    |-- __init__.py
    |-- config.py
    |-- detector.py
    `-- realtime_camera.py
```

## Run App

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

This opens a small launcher with three buttons:

- `Camera`
- `Image`
- `Video`

Click `Image` or `Video`, choose a file, and the app will detect emotion from it.

## Direct Camera

```powershell
python app.py --camera 0 --every 15
```

Use `--every 8` if your laptop is smooth enough.

## Direct Image

```powershell
python app.py --image "C:\path\to\photo.jpg"
```

## Direct Video

```powershell
python app.py --video "C:\path\to\video.mp4" --every 12
```

## Controls

- `Q` or `Esc`: quit
- `S`: save screenshot to `captures/`
- `+` / `-`: change analysis speed in camera/video mode
