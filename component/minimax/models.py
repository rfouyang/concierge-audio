"""MiniMax request models, constants, and service errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from component.common.models import ConciergeAudioError, GeneratedAudio, ValidationError


SUPPORTED_MODELS = (
    "speech-2.8-hd", "speech-2.8-turbo", "speech-2.6-hd", "speech-2.6-turbo",
    "speech-02-hd", "speech-02-turbo", "speech-01-hd", "speech-01-turbo",
)
SUPPORTED_EMOTIONS = (
    "happy", "sad", "angry", "fearful", "disgusted", "surprised", "calm",
    "fluent", "whisper",
)
SUPPORTED_SOUND_TAGS = (
    "laughs", "chuckle", "coughs", "clear-throat", "groans", "breath", "pant",
    "inhale", "exhale", "gasps", "sniffs", "sighs", "snorts", "burps",
    "lip-smacking", "humming", "hissing", "emm", "sneezes",
)
SUPPORTED_SOUND_EFFECTS = (
    "spacious_echo", "auditorium_echo", "lofi_telephone", "robotic",
)
SUPPORTED_LANGUAGE_BOOSTS = (
    "Chinese", "Chinese,Yue", "English", "Arabic", "Russian", "Spanish",
    "French", "Portuguese", "German", "Turkish", "Dutch", "Ukrainian",
    "Vietnamese", "Indonesian", "Japanese", "Italian", "Korean", "Thai",
    "Polish", "Romanian", "Greek", "Czech", "Finnish", "Hindi", "Bulgarian",
    "Danish", "Hebrew", "Malay", "Persian", "Slovak", "Swedish", "Croatian",
    "Filipino", "Hungarian", "Norwegian", "Slovenian", "Catalan", "Nynorsk",
    "Tamil", "Afrikaans", "auto",
)


class MinimaxApiError(ConciergeAudioError):
    """Raised when MiniMax rejects or cannot complete a request."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.trace_id = trace_id


@dataclass(frozen=True, slots=True)
class MinimaxTtsSegment:
    """One text span with an optional request-level MiniMax emotion."""

    text: str
    emotion: str | None


@dataclass(frozen=True, slots=True)
class MinimaxTtsRequest:
    """Validated user-adjustable MiniMax synthesis parameters."""

    text: str
    model: str
    voice_id: str
    language_boost: str
    speed: float
    volume: float
    pitch: int
    emotion: str | None
    text_normalization: bool
    modifier_pitch: int
    modifier_intensity: int
    modifier_timbre: int
    sound_effect: str | None
    segments: tuple[MinimaxTtsSegment, ...] = ()

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "MinimaxTtsRequest":
        try:
            return cls(
                text=str(values.get("text", "")),
                model=str(values.get("model", "speech-2.8-hd")),
                voice_id=str(values.get("voice_id", "")).strip(),
                language_boost=str(values.get("language_boost", "auto")),
                speed=float(values.get("speed", 1.0)),
                volume=float(values.get("volume", 1.0)),
                pitch=int(values.get("pitch", 0)),
                emotion=_optional_string(values.get("emotion")),
                text_normalization=_as_bool(values.get("text_normalization", False)),
                modifier_pitch=int(values.get("modifier_pitch", 0)),
                modifier_intensity=int(values.get("modifier_intensity", 0)),
                modifier_timbre=int(values.get("modifier_timbre", 0)),
                sound_effect=_optional_string(values.get("sound_effect")),
                segments=_tts_segments(values.get("segments")),
            )
        except (TypeError, ValueError) as error:
            raise ValidationError("请求中包含格式不正确的数值。") from error


def _tts_segments(value: Any) -> tuple[MinimaxTtsSegment, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValidationError("segments 必须是数组。")
    segments: list[MinimaxTtsSegment] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValidationError("segments 中的每一项必须是对象。")
        segments.append(
            MinimaxTtsSegment(
                text=str(item.get("text", "")),
                emotion=_optional_string(item.get("emotion")),
            )
        )
    return tuple(segments)


@dataclass(frozen=True, slots=True)
class AsyncTtsTask:
    task_id: str
    file_id: int | None
    usage_characters: int | None


@dataclass(frozen=True, slots=True)
class AsyncTtsResult:
    task_id: str
    status: str
    file_id: int | None
    generated_audio: GeneratedAudio | None = None


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


TtsRequest = MinimaxTtsRequest
TtsSegment = MinimaxTtsSegment
