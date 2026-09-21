"""Small, credit-consuming BytePlus Seed Speech integration smoke test.

Run explicitly with ``python -m tests.byteplus.live_byteplus_smoke``. The
ordinary unittest suite never imports or executes this module.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from component.byteplus.models import ByteplusStyleConfig, ByteplusTtsRequest
from component.byteplus.prompt_mapper import build_byteplus_prompt
from component.byteplus.tts_service import ByteplusTtsService
from config.settings import Settings
from util.byteplus_tts_helper import ByteplusTtsHelper
from util.wav_helper import WavHelper


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    settings = Settings.from_env()
    style = ByteplusStyleConfig(
        emotion="happy",
        intensity="moderate",
        social_tone="warm",
        communicative_intent="encourage",
        voice_texture=("soft",),
        pace="normal",
        pitch="normal",
        energy="medium",
    )
    request = ByteplusTtsRequest.from_mapping(
        {
            "text": "你好，我是 Unitree G1，很高兴见到你。",
            "voice_id": "zh_female_vv_uranus_bigtts",
            "speech_rate": 0,
            "loudness_rate": 0,
            "segments": [
                {
                    "text": "你好，我是 Unitree G1，很高兴见到你。",
                    "style": style.as_dict(),
                }
            ],
        }
    )
    service = ByteplusTtsService(
        byteplus_helper=ByteplusTtsHelper(
            api_key=settings.byteplus.api_key,
            base_url=settings.byteplus.api_base_url,
            resource_id=settings.byteplus.resource_id,
            user_id=settings.byteplus.user_id,
            connect_timeout_seconds=settings.byteplus.connect_timeout_seconds,
            read_timeout_seconds=settings.byteplus.read_timeout_seconds,
        ),
        wav_helper=WavHelper(
            required_sample_rate=settings.system.audio_sample_rate,
            required_channels=settings.system.audio_channels,
        ),
        max_segments=settings.byteplus.max_segments,
    )
    output_dir = PROJECT_ROOT / "debug" / "byteplus_live" / datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )
    output_dir.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {
        "provider": "byteplus",
        "voice_id": request.voice_id,
        "text": request.text,
        "style": style.as_dict(),
        "context_text": build_byteplus_prompt(style),
    }

    try:
        generated = service.synthesize(request)
        wav_path = output_dir / "styled_chinese.wav"
        wav_path.write_bytes(generated.audio)
        report.update(
            {
                "status": "passed",
                "request_ids": generated.trace_id.split(","),
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
        )
    except Exception as error:
        report.update(
            {
                "status": "failed",
                "error_type": type(error).__name__,
                "error": str(error),
            }
        )

    report_path = output_dir / "result.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(report_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
