"""MiniMax synthesis workflow and G1 audio invariants."""

from __future__ import annotations

import re
import time
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from component.common.models import GeneratedAudio, ValidationError
from component.minimax.models import (
    AsyncTtsResult,
    AsyncTtsTask,
    MinimaxApiError,
    MinimaxTtsRequest,
    SUPPORTED_EMOTIONS,
    SUPPORTED_LANGUAGE_BOOSTS,
    SUPPORTED_MODELS,
    SUPPORTED_SOUND_EFFECTS,
    SUPPORTED_SOUND_TAGS,
)
from util.minimax_tts_helper import MinimaxTtsHelper
from util.wav_helper import WavHelper


_PAUSE_PATTERN = re.compile(r"<#([^#]+)#>")
_SOUND_TAG_PATTERN = re.compile(
    r"\((" + "|".join(re.escape(tag) for tag in SUPPORTED_SOUND_TAGS) + r")\)"
)
_INLINE_EMOTION_PATTERN = re.compile(r"\{/?(?:happy|sad|angry|fearful|disgusted|surprised|neutral|fluent)\}")
_SEGMENT_EMOTIONS = frozenset(
    {"happy", "sad", "angry", "fearful", "disgusted", "surprised", "neutral", "fluent"}
)
_SEGMENT_EMOTION_TO_API = {"neutral": "calm"}


class MinimaxTtsService:
    """Validate user controls, synthesize speech, and verify G1-ready WAV."""

    SAMPLE_RATE = 16000
    CHANNELS = 1
    AUDIO_FORMAT = "wav"
    MAX_TEXT_CHARACTERS = 9999
    MAX_ASYNC_INLINE_CHARACTERS = 50000
    MAX_ASYNC_TEXT_CHARACTERS = 200000
    MAX_SEGMENTS = 50

    def __init__(
        self,
        *,
        minimax_helper: MinimaxTtsHelper,
        wav_helper: WavHelper,
        voice_cache_seconds: int,
        max_segments: int = 50,
    ) -> None:
        self.minimax_helper = minimax_helper
        self.wav_helper = wav_helper
        self.voice_cache_seconds = voice_cache_seconds
        self.max_segments = max_segments
        self._voice_cache: list[dict[str, Any]] | None = None
        self._voice_cache_deadline = 0.0

    @property
    def is_configured(self) -> bool:
        return self.minimax_helper.is_configured

    def synthesize(self, request: MinimaxTtsRequest) -> GeneratedAudio:
        """Run one synchronous MiniMax synthesis request."""

        self._validate_request(request, max_characters=self.MAX_TEXT_CHARACTERS)
        if any(segment.emotion for segment in request.segments):
            return self._synthesize_segments(request)
        return self._synthesize_single(request)

    def _synthesize_single(self, request: MinimaxTtsRequest) -> GeneratedAudio:
        response = self.minimax_helper.synthesize(self._build_payload(request))
        wav_info = self.wav_helper.inspect(response.audio)
        usage_characters = response.extra_info.get("usage_characters")
        return GeneratedAudio(
            audio=response.audio,
            trace_id=response.trace_id,
            wav_info=wav_info,
            usage_characters=(
                usage_characters if isinstance(usage_characters, int) else None
            ),
        )

    def _synthesize_segments(self, request: MinimaxTtsRequest) -> GeneratedAudio:
        generated_segments: list[GeneratedAudio] = []
        for segment in request.segments:
            if not segment.text.strip():
                continue
            segment_request = replace(
                request,
                text=segment.text,
                emotion=_SEGMENT_EMOTION_TO_API.get(
                    segment.emotion or "",
                    segment.emotion,
                ),
                segments=(),
            )
            generated_segments.append(self._synthesize_single(segment_request))

        if not generated_segments:
            raise ValidationError("分段 Emotion 中没有可朗读文本。")
        audio = self.wav_helper.concatenate(
            [generated.audio for generated in generated_segments]
        )
        wav_info = self.wav_helper.inspect(audio)
        usage_values = [
            generated.usage_characters
            for generated in generated_segments
            if generated.usage_characters is not None
        ]
        return GeneratedAudio(
            audio=audio,
            trace_id=",".join(
                generated.trace_id
                for generated in generated_segments
                if generated.trace_id
            ),
            wav_info=wav_info,
            usage_characters=sum(usage_values) if usage_values else None,
        )

    def start_async_synthesis(self, request: MinimaxTtsRequest) -> AsyncTtsTask:
        """Create a MiniMax asynchronous task for Long Text mode."""

        self._validate_request(
            request,
            max_characters=self.MAX_ASYNC_TEXT_CHARACTERS,
        )
        if any(segment.emotion for segment in request.segments):
            raise ValidationError("Long Text 暂不支持分段 Emotion，请关闭 Long Text 后生成。")
        text_file_id: int | None = None
        if len(request.text) > self.MAX_ASYNC_INLINE_CHARACTERS:
            text_file_id = self.minimax_helper.upload_async_text(request.text)
        response = self.minimax_helper.create_async_task(
            self._build_async_payload(request, text_file_id=text_file_id)
        )
        task_id = response.get("task_id")
        if not isinstance(task_id, (str, int)):
            raise MinimaxApiError("MiniMax 异步任务响应中没有 task_id。")
        file_id = response.get("file_id")
        usage_characters = response.get("usage_characters")
        return AsyncTtsTask(
            task_id=str(task_id),
            file_id=file_id if isinstance(file_id, int) else None,
            usage_characters=(
                usage_characters if isinstance(usage_characters, int) else None
            ),
        )

    def get_async_result(self, task_id: str) -> AsyncTtsResult:
        """Return task progress or a verified G1-ready WAV when complete."""

        if not task_id.isdigit():
            raise ValidationError("异步任务 ID 格式不正确。")
        response = self.minimax_helper.query_async_task(task_id)
        status_value = response.get("status")
        status = status_value.lower() if isinstance(status_value, str) else ""
        file_id = response.get("file_id")
        normalized_file_id = file_id if isinstance(file_id, int) else None
        if status == "processing":
            return AsyncTtsResult(task_id, status, normalized_file_id)
        if status in {"failed", "expired"}:
            message = "失败" if status == "failed" else "已过期"
            raise MinimaxApiError(f"MiniMax 异步语音任务{message}。")
        if status != "success" or normalized_file_id is None:
            raise MinimaxApiError("MiniMax 返回了未知的异步任务状态。")

        audio = self.minimax_helper.download_async_audio(normalized_file_id)
        wav_info = self.wav_helper.inspect(audio)
        generated = GeneratedAudio(
            audio=audio,
            trace_id=task_id,
            wav_info=wav_info,
            usage_characters=None,
        )
        return AsyncTtsResult(task_id, status, normalized_file_id, generated)

    def list_voices(self, *, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Return a normalized, briefly cached voice catalog."""

        now = time.monotonic()
        if (
            not force_refresh
            and self._voice_cache is not None
            and now < self._voice_cache_deadline
        ):
            return list(self._voice_cache)

        response = self.minimax_helper.get_voices()
        voices: list[dict[str, Any]] = []
        for category in ("system_voice", "voice_cloning", "voice_generation"):
            category_voices = response.get(category, [])
            if not isinstance(category_voices, list):
                continue
            for raw_voice in category_voices:
                if not isinstance(raw_voice, Mapping):
                    continue
                voice_id = raw_voice.get("voice_id")
                if not isinstance(voice_id, str) or not voice_id:
                    continue
                voice_name = raw_voice.get("voice_name")
                description = raw_voice.get("description")
                voices.append(
                    {
                        "voice_id": voice_id,
                        "voice_name": (
                            voice_name
                            if isinstance(voice_name, str) and voice_name
                            else voice_id
                        ),
                        "description": _normalize_description(description),
                        "category": category,
                    }
                )

        voices.sort(key=lambda item: (item["category"], item["voice_name"].lower()))
        self._voice_cache = voices
        self._voice_cache_deadline = now + self.voice_cache_seconds
        return list(voices)

    def _validate_request(
        self,
        request: MinimaxTtsRequest,
        *,
        max_characters: int,
    ) -> None:
        if not request.text.strip():
            raise ValidationError("请输入需要合成的文本。")
        if len(request.text) > max_characters:
            raise ValidationError(f"文本不能超过 {max_characters:,} 个字符。")
        if request.model not in SUPPORTED_MODELS:
            raise ValidationError("不支持所选的 MiniMax 模型。")
        if not request.voice_id:
            raise ValidationError("请选择或输入一个音色。")
        if request.language_boost not in SUPPORTED_LANGUAGE_BOOSTS:
            raise ValidationError("不支持所选的语言增强选项。")
        if not 0.5 <= request.speed <= 2.0:
            raise ValidationError("语速必须在 0.5 到 2.0 之间。")
        if not 0 < request.volume <= 10:
            raise ValidationError("音量必须大于 0 且不超过 10。")
        if not -12 <= request.pitch <= 12:
            raise ValidationError("音高必须在 -12 到 12 之间。")
        if request.emotion and request.emotion not in SUPPORTED_EMOTIONS:
            raise ValidationError("不支持所选的情绪。")
        if request.emotion == "whisper" and not request.model.startswith("speech-2.6-"):
            raise ValidationError("whisper 只支持 speech-2.6 系列模型。")
        if _INLINE_EMOTION_PATTERN.search(request.text):
            raise ValidationError(
                "公开 HTTP API 会朗读大括号 Emotion 标签；请改用 segments 字段。"
            )
        self._validate_segments(request)
        for value, label in (
            (request.modifier_pitch, "音色深浅"),
            (request.modifier_intensity, "音色强弱"),
            (request.modifier_timbre, "音色质感"),
        ):
            if not -100 <= value <= 100:
                raise ValidationError(f"{label}必须在 -100 到 100 之间。")
        if request.sound_effect and request.sound_effect not in SUPPORTED_SOUND_EFFECTS:
            raise ValidationError("不支持所选的声音效果。")

        self._validate_pauses(request.text)
        if _SOUND_TAG_PATTERN.search(request.text) and not request.model.startswith(
            "speech-2.8-"
        ):
            raise ValidationError("Sound Tag 只支持 speech-2.8 系列模型。")

    def _validate_segments(self, request: MinimaxTtsRequest) -> None:
        if not request.segments:
            return
        if len(request.segments) > self.max_segments:
            raise ValidationError(f"分段 Emotion 最多支持 {self.max_segments} 段。")
        if "".join(segment.text for segment in request.segments) != request.text:
            raise ValidationError("segments 拼接后的文本必须与 text 完全一致。")
        if request.emotion and any(segment.emotion for segment in request.segments):
            raise ValidationError("分段 Emotion 不能与全局 emotion 同时使用。")
        for segment in request.segments:
            if segment.emotion and segment.emotion not in _SEGMENT_EMOTIONS:
                raise ValidationError(f"不支持分段 Emotion：{segment.emotion}。")
            if segment.emotion and not segment.text.strip():
                raise ValidationError("分段 Emotion 中必须包含可朗读文本。")

    def _validate_pauses(self, text: str) -> None:
        for match in _PAUSE_PATTERN.finditer(text):
            try:
                seconds = float(match.group(1))
            except ValueError as error:
                raise ValidationError("Pause 必须使用 <#秒数#> 格式。") from error
            if not 0.01 <= seconds <= 99.99:
                raise ValidationError("Pause 时间必须在 0.01 到 99.99 秒之间。")
            if "." in match.group(1) and len(match.group(1).split(".", 1)[1]) > 2:
                raise ValidationError("Pause 时间最多保留两位小数。")
            if not text[: match.start()].strip() or not text[match.end() :].strip():
                raise ValidationError("Pause 必须放在两段可朗读文本之间。")
        if re.search(r"<#(?:[^#]+)#>\s*<#(?:[^#]+)#>", text):
            raise ValidationError("两个 Pause 标记不能连续使用。")

    def _build_payload(self, request: MinimaxTtsRequest) -> dict[str, Any]:
        payload = self._build_common_payload(request)
        payload.update(
            {
                "text": request.text,
                "stream": False,
                "output_format": "hex",
                "audio_setting": {
                    "sample_rate": self.SAMPLE_RATE,
                    "format": self.AUDIO_FORMAT,
                    "channel": self.CHANNELS,
                },
            }
        )
        return payload

    def _build_async_payload(
        self,
        request: MinimaxTtsRequest,
        *,
        text_file_id: int | None,
    ) -> dict[str, Any]:
        payload = self._build_common_payload(request)
        if text_file_id is None:
            payload["text"] = request.text
        else:
            payload["text_file_id"] = text_file_id
        payload["audio_setting"] = {
            "audio_sample_rate": self.SAMPLE_RATE,
            "format": self.AUDIO_FORMAT,
            "channel": self.CHANNELS,
        }
        return payload

    def _build_common_payload(self, request: MinimaxTtsRequest) -> dict[str, Any]:
        voice_setting: dict[str, Any] = {
            "voice_id": request.voice_id,
            "speed": request.speed,
            "vol": request.volume,
            "pitch": request.pitch,
            "text_normalization": request.text_normalization,
        }
        if request.emotion:
            voice_setting["emotion"] = request.emotion

        payload: dict[str, Any] = {
            "model": request.model,
            "language_boost": request.language_boost,
            "voice_setting": voice_setting,
        }

        if any(
            (
                request.modifier_pitch,
                request.modifier_intensity,
                request.modifier_timbre,
                request.sound_effect,
            )
        ):
            voice_modify: dict[str, Any] = {
                "pitch": request.modifier_pitch,
                "intensity": request.modifier_intensity,
                "timbre": request.modifier_timbre,
            }
            if request.sound_effect:
                voice_modify["sound_effects"] = request.sound_effect
            payload["voice_modify"] = voice_modify

        return payload


def _normalize_description(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(item for item in value if isinstance(item, str))
    return value if isinstance(value, str) else ""


TtsService = MinimaxTtsService
