"""Credit-consuming smoke test for MiniMax Async Long TTS.

Run explicitly with ``python -m tests.minimax.live_minimax_async_smoke``. Ordinary
unit tests never import or execute this module.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from component.minimax.models import MinimaxTtsRequest
from component.minimax.tts_service import MinimaxTtsService
from config.settings import Settings
from util.minimax_tts_helper import MinimaxTtsHelper
from util.wav_helper import WavHelper


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    settings = Settings.from_env()
    helper = MinimaxTtsHelper(
        api_key=settings.minimax.api_key,
        base_url=settings.minimax.api_base_url,
        connect_timeout_seconds=settings.minimax.connect_timeout_seconds,
        read_timeout_seconds=settings.minimax.read_timeout_seconds,
    )
    service = MinimaxTtsService(
        minimax_helper=helper,
        wav_helper=WavHelper(required_sample_rate=16000, required_channels=1),
        voice_cache_seconds=settings.minimax.voice_cache_seconds,
        max_segments=settings.minimax.max_segments,
    )
    synthesis_request = MinimaxTtsRequest.from_mapping(
        {
            "text": "This is a short asynchronous audio test for Unitree G1.",
            "model": "speech-2.8-hd",
            "voice_id": "English_expressive_narrator",
            "language_boost": "English",
        }
    )
    output_dir = (
        PROJECT_ROOT
        / "debug"
        / "minimax_async_live"
        / datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    output_dir.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {
        "status": "started",
        "request": service._build_async_payload(  # noqa: SLF001
            synthesis_request,
            text_file_id=None,
        ),
    }

    try:
        if len(sys.argv) > 1:
            task_id = sys.argv[1]
            report.pop("request", None)
            report.update(
                {
                    "task_id": task_id,
                    "reused_existing_task": True,
                    "request_note": "Task was created outside this smoke-test process.",
                }
            )
        else:
            task = service.start_async_synthesis(synthesis_request)
            task_id = task.task_id
            report.update(
                {
                    "task_id": task_id,
                    "file_id": task.file_id,
                    "usage_characters": task.usage_characters,
                }
            )
        for query_number in range(1, 61):
            result = service.get_async_result(task_id)
            report["query_count"] = query_number
            report["status"] = result.status
            if result.generated_audio is not None:
                wav_path = output_dir / "async_direct_text.wav"
                wav_path.write_bytes(result.generated_audio.audio)
                report["wav"] = {
                    "path": wav_path.name,
                    "sample_rate": result.generated_audio.wav_info.sample_rate,
                    "channels": result.generated_audio.wav_info.channels,
                    "sample_width_bytes": (
                        result.generated_audio.wav_info.sample_width_bytes
                    ),
                    "duration_seconds": (
                        result.generated_audio.wav_info.duration_seconds
                    ),
                    "size_bytes": len(result.generated_audio.audio),
                }
                break
            time.sleep(2)
        else:
            raise TimeoutError("MiniMax async task did not finish within 120 seconds.")
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
    print(json.dumps(report, ensure_ascii=True, indent=2))
    if report["status"] != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
