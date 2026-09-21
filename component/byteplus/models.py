"""BytePlus request models and provider errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from component.common.models import ConciergeAudioError, ValidationError


class ByteplusApiError(ConciergeAudioError):
    """Raised when BytePlus rejects or cannot complete a request."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id


@dataclass(frozen=True, slots=True)
class ByteplusStyleConfig:
    emotion: str = "neutral"
    intensity: str = "subtle"
    social_tone: str = "neutral"
    mental_state: tuple[str, ...] = ()
    communicative_intent: str = "inform"
    voice_texture: tuple[str, ...] = ("normal",)
    pace: str = "normal"
    pitch: str = "normal"
    energy: str = "medium"
    preset_id: str | None = None

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "ByteplusStyleConfig":
        return cls(
            emotion=str(values.get("emotion", "neutral")),
            intensity=str(values.get("intensity", "subtle")),
            social_tone=str(values.get("social_tone", "neutral")),
            mental_state=_string_tuple(values.get("mental_state")),
            communicative_intent=str(
                values.get("communicative_intent", "inform")
            ),
            voice_texture=_string_tuple(
                values.get("voice_texture"),
                default=("normal",),
            ),
            pace=str(values.get("pace", "normal")),
            pitch=str(values.get("pitch", "normal")),
            energy=str(values.get("energy", "medium")),
            preset_id=str(values["preset_id"]) if values.get("preset_id") else None,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "emotion": self.emotion,
            "intensity": self.intensity,
            "social_tone": self.social_tone,
            "mental_state": list(self.mental_state),
            "communicative_intent": self.communicative_intent,
            "voice_texture": list(self.voice_texture),
            "pace": self.pace,
            "pitch": self.pitch,
            "energy": self.energy,
            "preset_id": self.preset_id,
        }


@dataclass(frozen=True, slots=True)
class ByteplusTtsSegment:
    text: str
    style: ByteplusStyleConfig | None


@dataclass(frozen=True, slots=True)
class ByteplusTtsRequest:
    text: str
    voice_id: str
    speech_rate: int
    loudness_rate: int
    segments: tuple[ByteplusTtsSegment, ...] = ()

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "ByteplusTtsRequest":
        try:
            return cls(
                text=str(values.get("text", "")),
                voice_id=str(values.get("voice_id", "")).strip(),
                speech_rate=int(values.get("speech_rate", 0)),
                loudness_rate=int(values.get("loudness_rate", 0)),
                segments=_segments(values.get("segments")),
            )
        except (TypeError, ValueError) as error:
            raise ValidationError("BytePlus 请求中包含格式不正确的数值。") from error


def _segments(value: Any) -> tuple[ByteplusTtsSegment, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValidationError("segments 必须是数组。")
    result: list[ByteplusTtsSegment] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValidationError("segments 中的每一项必须是对象。")
        raw_style = item.get("style")
        if raw_style is not None and not isinstance(raw_style, Mapping):
            raise ValidationError("segment.style 必须是对象或 null。")
        result.append(
            ByteplusTtsSegment(
                text=str(item.get("text", "")),
                style=(
                    ByteplusStyleConfig.from_mapping(raw_style)
                    if isinstance(raw_style, Mapping)
                    else None
                ),
            )
        )
    return tuple(result)


def _string_tuple(value: Any, *, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    if value is None:
        return default
    if not isinstance(value, list):
        raise ValidationError("多选风格参数必须是数组。")
    return tuple(str(item) for item in value)
