from dataclasses import dataclass


@dataclass(frozen=True)
class EmotionStyle:
    label: str
    color_bgr: tuple[int, int, int]
    accent_hex: str


EMOTION_STYLES: dict[str, EmotionStyle] = {
    "angry": EmotionStyle("Angry", (76, 76, 255), "#ff4d6d"),
    "disgust": EmotionStyle("Disgust", (84, 184, 79), "#2f9e44"),
    "fear": EmotionStyle("Fear", (211, 92, 255), "#8338ec"),
    "happy": EmotionStyle("Happy", (35, 190, 255), "#ffb703"),
    "sad": EmotionStyle("Sad", (255, 128, 35), "#3a86ff"),
    "surprise": EmotionStyle("Surprise", (48, 214, 200), "#20c997"),
    "neutral": EmotionStyle("Neutral", (150, 150, 150), "#687083"),
}

DEFAULT_STYLE = EmotionStyle("Unknown", (255, 255, 255), "#171923")
