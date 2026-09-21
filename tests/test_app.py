from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Any

from app.main import create_app
from component.byteplus.models import ByteplusStyleConfig
from component.common.models import GeneratedAudio, WavInfo
from component.minimax.models import AsyncTtsResult, AsyncTtsTask


class FakeTtsService:
    is_configured = True
    SAMPLE_RATE = 16000
    CHANNELS = 1
    AUDIO_FORMAT = "wav"

    def list_voices(self, *, force_refresh: bool = False) -> list[dict[str, str]]:
        return [
            {
                "voice_id": "voice-test",
                "voice_name": "Test Voice",
                "description": "For tests",
                "category": "system_voice",
            }
        ]

    def synthesize(self, request: Any) -> GeneratedAudio:
        from tests.minimax.test_tts_service import make_wav

        return GeneratedAudio(
            audio=make_wav(),
            trace_id="route-trace",
            wav_info=WavInfo(
                sample_rate=16000,
                channels=1,
                sample_width_bytes=2,
                frame_count=1600,
                duration_seconds=0.1,
            ),
            usage_characters=len(request.text),
        )

    def start_async_synthesis(self, request: Any) -> AsyncTtsTask:
        return AsyncTtsTask(
            task_id="123",
            file_id=None,
            usage_characters=len(request.text),
        )

    def get_async_result(self, task_id: str) -> AsyncTtsResult:
        if task_id == "456":
            return AsyncTtsResult(task_id, "processing", None)
        return AsyncTtsResult(
            task_id,
            "success",
            789,
            self.synthesize(type("Request", (), {"text": "async"})()),
        )


class FakeByteplusService:
    is_configured = True
    SAMPLE_RATE = 16000
    CHANNELS = 1
    AUDIO_FORMAT = "wav"

    def list_voices(self) -> list[dict[str, str]]:
        return [
            {
                "voice_id": "zh_female_vv_uranus_bigtts",
                "voice_name": "Vivi",
                "language": "Chinese",
                "gender": "Female",
                "category": "Official TTS 2.0",
                "description": "BytePlus official voice",
            }
        ]

    def list_presets(self) -> list[dict[str, Any]]:
        return [{"id": "001", "name": "平静陈述", "style": {"emotion": "neutral"}}]

    def preview_prompt(self, style: ByteplusStyleConfig) -> str:
        return f"用{style.emotion}的语气说。"

    def synthesize(self, request: Any) -> GeneratedAudio:
        from tests.minimax.test_tts_service import make_wav

        return GeneratedAudio(
            audio=make_wav(),
            trace_id="byteplus-request",
            wav_info=WavInfo(16000, 1, 2, 1600, 0.1),
            usage_characters=len(request.text),
        )


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.history_directory = TemporaryDirectory()
        self.addCleanup(self.history_directory.cleanup)
        self.history_root = Path(self.history_directory.name)
        app = create_app(
            history_root=self.history_root,
            tts_service=FakeTtsService(),  # type: ignore[arg-type]
            byteplus_tts_service=FakeByteplusService(),  # type: ignore[arg-type]
        )
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_history_survives_restart_and_supports_download_delete(self):
        for provider in ("minimax", "byteplus"):
            response = self.client.post(f"/api/{provider}/tts", json={"text": "Persistent text", "voice_id": "voice-test"})
            self.assertEqual(response.status_code, 200)
            records = self.client.get(f"/api/{provider}/history").json["history"]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["text"], "Persistent text")
            self.assertGreater(records[0]["duration_seconds"], 0)
            record_id = records[0]["id"]
            restarted = create_app(history_root=self.history_root).test_client()
            self.assertEqual(len(restarted.get(f"/api/{provider}/history").json["history"]), 1)
            download = restarted.get(f"/api/{provider}/history/{record_id}/audio?download=1")
            self.assertEqual(download.data, response.data)
            self.assertIn("attachment", download.headers["Content-Disposition"])
            download.close()
            self.assertEqual(restarted.delete(f"/api/{provider}/history/{record_id}").status_code, 204)
            self.assertFalse((self.history_root / provider / f"{record_id}.wav").exists())
            self.assertEqual(restarted.get(f"/api/{provider}/history/{record_id}/audio").status_code, 404)

    def test_async_history_keeps_original_text_without_duplicates(self):
        self.client.post("/api/minimax/tts/async", json={"text": "Original long text", "voice_id": "voice-test"})
        for _ in range(2):
            self.assertEqual(self.client.get("/api/minimax/tts/async/123").status_code, 200)
        records = self.client.get("/api/minimax/history").json["history"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["text"], "Original long text")

    def test_history_rejects_invalid_paths(self):
        self.assertEqual(self.client.get("/api/unknown/history").status_code, 404)
        self.assertEqual(self.client.delete("/api/minimax/history/invalid").status_code, 404)

    def test_index_loads_studio(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Concierge Audio", response.data)
        self.assertIn(b"Speech Synthesis", response.data)
        self.assertIn(b'id="emotion-button"', response.data)
        self.assertIn(b"200,000", response.data)

    def test_byteplus_page_loads_studio(self) -> None:
        response = self.client.get("/byteplus")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Seed Speech Synthesis", response.data)
        self.assertIn(b'id="emotion-panel"', response.data)

    def test_health_reports_g1_profile(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["audio"]["sample_rate"], 16000)

    def test_namespaced_minimax_health_is_available(self) -> None:
        response = self.client.get("/api/minimax/health")
        self.assertEqual(response.status_code, 200)

    def test_byteplus_catalog_and_presets_are_available(self) -> None:
        voices = self.client.get("/api/byteplus/voices")
        presets = self.client.get("/api/byteplus/presets")
        self.assertEqual(voices.status_code, 200)
        self.assertEqual(voices.get_json()["voices"][0]["voice_name"], "Vivi")
        self.assertEqual(presets.status_code, 200)
        self.assertEqual(presets.get_json()["presets"][0]["id"], "001")

    def test_byteplus_prompt_preview_uses_structured_style(self) -> None:
        response = self.client.post(
            "/api/byteplus/prompt-preview",
            json={"style": {"emotion": "happy"}},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("happy", response.get_json()["prompt"])

    def test_byteplus_tts_returns_verified_wav(self) -> None:
        response = self.client.post(
            "/api/byteplus/tts",
            json={
                "text": "你好",
                "voice_id": "zh_female_vv_uranus_bigtts",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "audio/wav")
        self.assertEqual(response.headers["X-BytePlus-Request-Id"], "byteplus-request")

    def test_tts_returns_verified_wav(self) -> None:
        response = self.client.post(
            "/api/tts",
            json={
                "text": "hello",
                "voice_id": "voice-test",
                "model": "speech-2.8-hd",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "audio/wav")
        self.assertEqual(response.headers["X-Audio-Sample-Rate"], "16000")
        self.assertEqual(response.headers["X-Minimax-Trace-Id"], "route-trace")

    def test_tts_rejects_non_json_body(self) -> None:
        response = self.client.post("/api/tts", data="hello")
        self.assertEqual(response.status_code, 400)
        self.assertIn("JSON", response.get_json()["error"])

    def test_async_tts_creation_returns_task(self) -> None:
        response = self.client.post(
            "/api/tts/async",
            json={
                "text": "long hello",
                "voice_id": "voice-test",
                "model": "speech-2.8-hd",
            },
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json()["task_id"], "123")

    def test_async_tts_query_reports_processing(self) -> None:
        response = self.client.get("/api/tts/async/456")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json()["status"], "processing")

    def test_async_tts_query_returns_verified_wav(self) -> None:
        response = self.client.get("/api/tts/async/123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "audio/wav")
        self.assertEqual(response.headers["X-Audio-Sample-Rate"], "16000")


def demo_tests() -> None:
    unittest.main(module=__name__, verbosity=2)


def main() -> None:
    demo_tests()


if __name__ == "__main__":
    main()
