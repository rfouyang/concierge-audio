"""BytePlus synthesis workflow and Unitree G1 audio invariants."""

from __future__ import annotations

from component.byteplus.models import (
    ByteplusStyleConfig,
    ByteplusTtsRequest,
    ByteplusTtsSegment,
)
from component.byteplus.presets import list_presets
from component.byteplus.prompt_mapper import build_byteplus_prompt, validate_style
from component.byteplus.voices import list_voices
from component.common.models import GeneratedAudio, ValidationError
from util.byteplus_tts_helper import ByteplusTtsHelper
from util.wav_helper import WavHelper


class ByteplusTtsService:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    AUDIO_FORMAT = "wav"
    MAX_TEXT_CHARACTERS = 10000

    def __init__(
        self,
        *,
        byteplus_helper: ByteplusTtsHelper,
        wav_helper: WavHelper,
        max_segments: int,
    ) -> None:
        self.byteplus_helper = byteplus_helper
        self.wav_helper = wav_helper
        self.max_segments = max_segments

    @property
    def is_configured(self) -> bool:
        return self.byteplus_helper.is_configured

    def list_voices(self) -> list[dict[str, object]]:
        return list_voices()

    def list_presets(self) -> list[dict[str, object]]:
        return list_presets()

    def preview_prompt(self, style: ByteplusStyleConfig) -> str:
        return build_byteplus_prompt(style)

    def synthesize(self, request: ByteplusTtsRequest) -> GeneratedAudio:
        self._validate_request(request)
        segments = self._effective_segments(request)
        generated: list[GeneratedAudio] = []
        segment_details = []
        for segment in segments:
            if not segment.text.strip():
                continue
            prompt = build_byteplus_prompt(segment.style) if segment.style else None
            response = self.byteplus_helper.synthesize(
                text=segment.text,
                voice_id=request.voice_id,
                sample_rate=self.SAMPLE_RATE,
                speech_rate=request.speech_rate,
                loudness_rate=request.loudness_rate,
                context_text=prompt,
            )
            segment_details.append({
                "text": segment.text,
                "style": segment.style.as_dict() if segment.style else None,
                "context_text": prompt,
                "request_id": response.request_id,
            })
            audio = self.wav_helper.from_pcm(response.pcm, sample_width_bytes=2)
            generated.append(
                GeneratedAudio(
                    audio=audio,
                    trace_id=response.request_id,
                    wav_info=self.wav_helper.inspect(audio),
                    usage_characters=len(segment.text),
                )
            )
        if not generated:
            raise ValidationError("BytePlus 分段中没有可朗读文本。")
        audio = (
            generated[0].audio
            if len(generated) == 1
            else self.wav_helper.concatenate([item.audio for item in generated])
        )
        return GeneratedAudio(
            audio=audio,
            trace_id=",".join(item.trace_id for item in generated),
            wav_info=self.wav_helper.inspect(audio),
            usage_characters=sum(item.usage_characters or 0 for item in generated),
            synthesis_details={
                "voice_id": request.voice_id,
                "speech_rate": request.speech_rate,
                "loudness_rate": request.loudness_rate,
                "sample_rate": self.SAMPLE_RATE,
                "segments": segment_details,
            },
        )

    def _validate_request(self, request: ByteplusTtsRequest) -> None:
        if not request.text.strip():
            raise ValidationError("请输入需要合成的文本。")
        if len(request.text) > self.MAX_TEXT_CHARACTERS:
            raise ValidationError(
                f"BytePlus 文本不能超过 {self.MAX_TEXT_CHARACTERS:,} 个字符。"
            )
        if not request.voice_id:
            raise ValidationError("请选择或输入一个 BytePlus 音色。")
        if not -50 <= request.speech_rate <= 100:
            raise ValidationError("BytePlus 语速必须在 -50 到 100 之间。")
        if not -50 <= request.loudness_rate <= 100:
            raise ValidationError("BytePlus 音量必须在 -50 到 100 之间。")
        if len(request.segments) > self.max_segments:
            raise ValidationError(f"BytePlus 风格最多支持 {self.max_segments} 段。")
        if request.segments and "".join(item.text for item in request.segments) != request.text:
            raise ValidationError("segments 拼接后的文本必须与 text 完全一致。")
        for segment in request.segments:
            if segment.style:
                if not segment.text.strip():
                    raise ValidationError("带风格的 segment 必须包含可朗读文本。")
                validate_style(segment.style)

    @staticmethod
    def _effective_segments(request: ByteplusTtsRequest) -> list[ByteplusTtsSegment]:
        if not request.segments:
            return [ByteplusTtsSegment(text=request.text, style=None)]
        merged: list[ByteplusTtsSegment] = []
        for segment in request.segments:
            if merged and merged[-1].style == segment.style:
                previous = merged[-1]
                merged[-1] = ByteplusTtsSegment(
                    text=previous.text + segment.text,
                    style=previous.style,
                )
            else:
                merged.append(segment)
        return merged
