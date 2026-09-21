"""Small, credit-consuming MiniMax integration smoke test.

Run explicitly with ``python -m tests.minimax.live_minimax_smoke``. The ordinary
unittest suite never imports or executes this module.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from component.minimax.models import MinimaxTtsRequest
from component.minimax.tts_service import MinimaxTtsService
from config.settings import Settings
from util.minimax_tts_helper import MinimaxSynthesisResponse, MinimaxTtsHelper
from util.wav_helper import WavHelper


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class CapturingMinimaxHelper:
    """Record the exact JSON payload while delegating the real HTTP call."""

    def __init__(self, delegate: MinimaxTtsHelper) -> None:
        self.delegate = delegate
        self.last_payload: dict[str, Any] | None = None

    @property
    def is_configured(self) -> bool:
        return self.delegate.is_configured

    def synthesize(self, payload: Mapping[str, Any]) -> MinimaxSynthesisResponse:
        self.last_payload = dict(payload)
        return self.delegate.synthesize(payload)

    def get_voices(self) -> Mapping[str, Any]:
        return self.delegate.get_voices()


def make_request(**overrides: Any) -> MinimaxTtsRequest:
    values: dict[str, Any] = {
        "text": "Hello from Unitree G1.",
        "model": "speech-2.8-hd",
        "voice_id": "English_expressive_narrator",
        "language_boost": "English",
        "speed": 1.0,
        "volume": 1.0,
        "pitch": 0,
        "emotion": None,
        "text_normalization": False,
        "modifier_pitch": 0,
        "modifier_intensity": 0,
        "modifier_timbre": 0,
        "sound_effect": None,
    }
    values.update(overrides)
    return MinimaxTtsRequest.from_mapping(values)


def main() -> None:
    settings = Settings.from_env()
    helper = CapturingMinimaxHelper(
        MinimaxTtsHelper(
            api_key=settings.minimax.api_key,
            base_url=settings.minimax.api_base_url,
            connect_timeout_seconds=settings.minimax.connect_timeout_seconds,
            read_timeout_seconds=settings.minimax.read_timeout_seconds,
        )
    )
    service = MinimaxTtsService(
        minimax_helper=helper,  # type: ignore[arg-type]
        wav_helper=WavHelper(required_sample_rate=16000, required_channels=1),
        voice_cache_seconds=settings.minimax.voice_cache_seconds,
        max_segments=settings.minimax.max_segments,
    )
    cases = {
        "emotion_pause": make_request(
            text="Hello <#0.25#> welcome.",
            speed=1.1,
            volume=0.9,
            pitch=1,
            emotion="happy",
        ),
        "sound_tag_modifier": make_request(
            text="Hello (laughs).",
            modifier_pitch=-10,
            modifier_intensity=10,
            modifier_timbre=5,
            sound_effect="robotic",
        ),
        "fluent_28": make_request(text="Welcome.", emotion="fluent"),
    }

    output_dir = PROJECT_ROOT / "debug" / "minimax_live" / datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )
    output_dir.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {"cases": {}}

    for name, request in cases.items():
        try:
            generated = service.synthesize(request)
            wav_path = output_dir / f"{name}.wav"
            wav_path.write_bytes(generated.audio)
            report["cases"][name] = {
                "status": "passed",
                "request": helper.last_payload,
                "trace_id": generated.trace_id,
                "usage_characters": generated.usage_characters,
                "wav": {
                    "path": wav_path.name,
                    "sample_rate": generated.wav_info.sample_rate,
                    "channels": generated.wav_info.channels,
                    "sample_width_bytes": generated.wav_info.sample_width_bytes,
                    "duration_seconds": generated.wav_info.duration_seconds,
                    "size_bytes": len(generated.audio),
                },
            }
        except Exception as error:
            report["cases"][name] = {
                "status": "failed",
                "request": helper.last_payload,
                "error_type": type(error).__name__,
                "error": str(error),
            }

    report_path = output_dir / "result.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(report_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if any(case["status"] != "passed" for case in report["cases"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
