from __future__ import annotations

import os
import sys
from dataclasses import dataclass

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import cv2
import numpy as np
from deepface import DeepFace

from src.config import DEFAULT_STYLE, EMOTION_STYLES


@dataclass(frozen=True)
class FaceEmotion:
    dominant_emotion: str
    confidence: float
    region: dict[str, int]
    scores: dict[str, float]


@dataclass(frozen=True)
class DetectionResult:
    faces: list[FaceEmotion]
    annotated_image: np.ndarray


def analyze_emotions(image_rgb: np.ndarray) -> DetectionResult:
    """Detect faces and emotions in an RGB image."""
    detections = DeepFace.analyze(
        img_path=image_rgb,
        actions=["emotion"],
        detector_backend="opencv",
        enforce_detection=False,
        silent=True,
    )

    if isinstance(detections, dict):
        detections = [detections]

    faces = [_parse_detection(item) for item in detections if _has_face_region(item)]
    annotated = draw_emotion_overlays(image_rgb, faces)
    return DetectionResult(faces=faces, annotated_image=annotated)


def draw_emotion_overlays(image_rgb: np.ndarray, faces: list[FaceEmotion]) -> np.ndarray:
    canvas = image_rgb.copy()

    for face in faces:
        region = face.region
        x, y = max(0, region["x"]), max(0, region["y"])
        w, h = max(1, region["w"]), max(1, region["h"])
        style = EMOTION_STYLES.get(face.dominant_emotion.lower(), DEFAULT_STYLE)
        label = f"{style.label} {face.confidence:.0f}%"

        color = style.color_bgr[::-1]
        cv2.rectangle(canvas, (x, y), (x + w, y + h), color, 3)
        cv2.rectangle(canvas, (x, max(0, y - 32)), (x + max(150, w), y), color, -1)
        cv2.putText(
            canvas,
            label,
            (x + 9, max(22, y - 9)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.68,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

    return canvas


def _parse_detection(item: dict) -> FaceEmotion:
    emotion_scores = {
        name: float(score)
        for name, score in sorted(
            item.get("emotion", {}).items(),
            key=lambda pair: float(pair[1]),
            reverse=True,
        )
    }
    dominant = str(item.get("dominant_emotion", "neutral")).lower()

    return FaceEmotion(
        dominant_emotion=dominant,
        confidence=emotion_scores.get(dominant, 0.0),
        region=_parse_region(item.get("region", {}) or {}),
        scores=emotion_scores,
    )


def _has_face_region(item: dict) -> bool:
    region = _parse_region(item.get("region", {}) or {})
    return region["w"] > 0 and region["h"] > 0


def _parse_region(region: dict) -> dict[str, int]:
    return {
        "x": _safe_int(region.get("x")),
        "y": _safe_int(region.get("y")),
        "w": _safe_int(region.get("w")),
        "h": _safe_int(region.get("h")),
    }


def _safe_int(value, default: int = 0) -> int:
    if value is None or isinstance(value, (tuple, list, dict)):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
