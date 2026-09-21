from __future__ import annotations

import io
import unittest
import wave
from typing import Any, Mapping

from component.common.models import ValidationError
from component.minimax.models import MinimaxTtsRequest
from component.minimax.tts_service import MinimaxTtsService
from util.minimax_tts_helper import MinimaxSynthesisResponse
from util.wav_helper import WavHelper


class FakeMinimaxHelper:
    def __init__(self, *, audio: bytes | None = None) -> None:
        self.audio = audio or make_wav()
        self.is_configured = True
        self.last_payload: Mapping[str, Any] | None = None
        self.payloads: list[Mapping[str, Any]] = []
        self.async_payload: Mapping[str, Any] | None = None
        self.uploaded_text: str | None = None
        self.async_query_response: Mapping[str, Any] = {
            "status": "Processing",
            "task_id": 321,
        }

    def synthesize(self, payload: Mapping[str, Any]) -> MinimaxSynthesisResponse:
        self.last_payload = payload
        self.payloads.append(payload)
        return MinimaxSynthesisResponse(
            audio=self.audio,
            trace_id="trace-test",
            extra_info={"usage_characters": len(str(payload["text"]))},
        )

    def get_voices(self) -> Mapping[str, Any]:
        return {
            "system_voice": [
                {
                    "voice_id": "English_expressive_narrator",
                    "voice_name": "Expressive Narrator",
                    "description": ["English narrator"],
                }
            ],
            "voice_cloning": [],
            "voice_generation": [],
        }

    def upload_async_text(self, text: str) -> int:
        self.uploaded_text = text
        return 123

    def create_async_task(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self.async_payload = payload
        return {"task_id": 321, "file_id": 456, "usage_characters": 12}

    def query_async_task(self, task_id: str) -> Mapping[str, Any]:
        return self.async_query_response

    def download_file(self, file_id: int) -> bytes:
        return self.audio

    def download_async_audio(self, file_id: int) -> bytes:
        return self.audio


def make_wav(*, sample_rate: int = 16000, channels: int = 1) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * (sample_rate * channels // 10))
    return output.getvalue()


def make_request(**overrides: Any) -> MinimaxTtsRequest:
    values: dict[str, Any] = {
        "text": "Hello from Unitree G1.",
        "model": "speech-2.8-hd",
        "voice_id": "English_expressive_narrator",
        "language_boost": "English",
        "speed": 1,
        "volume": 1,
        "pitch": 0,
        "emotion": None,
        "text_normalization": False,
        "modifier_pitch": 0,
        "modifier_intensity": 0,
        "modifier_timbre": 0,
        "sound_effect": None,
        "segments": None,
    }
    values.update(overrides)
    return MinimaxTtsRequest.from_mapping(values)


class MinimaxTtsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.minimax = FakeMinimaxHelper()
        self.service = MinimaxTtsService(
            minimax_helper=self.minimax,  # type: ignore[arg-type]
            wav_helper=WavHelper(required_sample_rate=16000, required_channels=1),
            voice_cache_seconds=300,
        )

    def test_synthesis_always_requests_g1_audio_profile(self) -> None:
        generated = self.service.synthesize(make_request())

        self.assertEqual(generated.wav_info.sample_rate, 16000)
        self.assertEqual(generated.wav_info.channels, 1)
        self.assertIsNotNone(self.minimax.last_payload)
        self.assertEqual(
            self.minimax.last_payload["audio_setting"],  # type: ignore[index]
            {"sample_rate": 16000, "format": "wav", "channel": 1},
        )
        self.assertEqual(self.minimax.last_payload["output_format"], "hex")  # type: ignore[index]

    def test_rejects_sound_tag_on_non_28_model(self) -> None:
        with self.assertRaisesRegex(ValidationError, "Sound Tag"):
            self.service.synthesize(
                make_request(text="Hello (laughs)", model="speech-2.6-hd")
            )

    def test_rejects_whisper_on_non_26_model(self) -> None:
        with self.assertRaisesRegex(ValidationError, "whisper"):
            self.service.synthesize(make_request(emotion="whisper"))

    def test_accepts_fluent_on_28_model(self) -> None:
        self.service.synthesize(make_request(emotion="fluent"))
        self.assertEqual(
            self.minimax.last_payload["voice_setting"]["emotion"],  # type: ignore[index]
            "fluent",
        )

    def test_segmented_emotions_make_clean_requests_and_concatenate_wav(self) -> None:
        text = "好消息！但是我要离开了。"
        generated = self.service.synthesize(
            make_request(
                text=text,
                segments=[
                    {"text": "好消息！", "emotion": "happy"},
                    {"text": "但是我要离开了。", "emotion": "sad"},
                ],
            )
        )

        self.assertEqual(len(self.minimax.payloads), 2)
        self.assertEqual(
            [payload["text"] for payload in self.minimax.payloads],
            ["好消息！", "但是我要离开了。"],
        )
        self.assertEqual(
            [payload["voice_setting"]["emotion"] for payload in self.minimax.payloads],  # type: ignore[index]
            ["happy", "sad"],
        )
        self.assertNotIn("Happy", str(self.minimax.payloads))
        self.assertAlmostEqual(generated.wav_info.duration_seconds, 0.2)

    def test_segmented_neutral_maps_to_global_calm(self) -> None:
        self.service.synthesize(
            make_request(
                text="欢迎。",
                segments=[{"text": "欢迎。", "emotion": "neutral"}],
            )
        )
        self.assertEqual(
            self.minimax.last_payload["voice_setting"]["emotion"],  # type: ignore[index]
            "calm",
        )

    def test_rejects_inline_emotion_markup_to_prevent_it_being_spoken(self) -> None:
        with self.assertRaisesRegex(ValidationError, "会朗读"):
            self.service.synthesize(make_request(text="{happy}欢迎。{/happy}"))

    def test_rejects_unknown_segment_emotion(self) -> None:
        with self.assertRaisesRegex(ValidationError, "excited"):
            self.service.synthesize(
                make_request(
                    text="欢迎。",
                    segments=[{"text": "欢迎。", "emotion": "excited"}],
                )
            )

    def test_rejects_segments_that_do_not_match_plain_text(self) -> None:
        with self.assertRaisesRegex(ValidationError, "完全一致"):
            self.service.synthesize(
                make_request(
                    text="欢迎。",
                    segments=[{"text": "不一致。", "emotion": "happy"}],
                )
            )

    def test_rejects_global_and_segment_emotion_together(self) -> None:
        with self.assertRaisesRegex(ValidationError, "不能与全局"):
            self.service.synthesize(
                make_request(
                    text="欢迎。",
                    emotion="calm",
                    segments=[{"text": "欢迎。", "emotion": "happy"}],
                )
            )

    def test_builds_live_verified_control_payload(self) -> None:
        self.service.synthesize(
            make_request(
                text="Hello <#0.25#> (laughs) welcome.",
                speed=1.1,
                volume=0.9,
                pitch=1,
                emotion="calm",
                text_normalization=True,
                modifier_pitch=-10,
                modifier_intensity=10,
                modifier_timbre=5,
                sound_effect="robotic",
            )
        )

        self.assertIsNotNone(self.minimax.last_payload)
        self.assertEqual(
            self.minimax.last_payload["voice_setting"],  # type: ignore[index]
            {
                "voice_id": "English_expressive_narrator",
                "speed": 1.1,
                "vol": 0.9,
                "pitch": 1,
                "text_normalization": True,
                "emotion": "calm",
            },
        )
        self.assertEqual(
            self.minimax.last_payload["voice_modify"],  # type: ignore[index]
            {
                "pitch": -10,
                "intensity": 10,
                "timbre": 5,
                "sound_effects": "robotic",
            },
        )

    def test_accepts_pause_with_two_decimal_places(self) -> None:
        generated = self.service.synthesize(
            make_request(text="Hello <#0.25#> welcome.")
        )
        self.assertEqual(generated.trace_id, "trace-test")

    def test_rejects_consecutive_pauses(self) -> None:
        with self.assertRaisesRegex(ValidationError, "不能连续"):
            self.service.synthesize(
                make_request(text="Hello <#0.5#> <#1.0#> welcome.")
            )

    def test_rejects_pause_at_end_of_text(self) -> None:
        with self.assertRaisesRegex(ValidationError, "两段可朗读文本之间"):
            self.service.synthesize(make_request(text="Hello <#0.5#>"))

    def test_rejects_unknown_language_boost(self) -> None:
        with self.assertRaisesRegex(ValidationError, "语言增强"):
            self.service.synthesize(make_request(language_boost="Unknown"))

    def test_normalizes_voice_catalog(self) -> None:
        voices = self.service.list_voices()
        self.assertEqual(len(voices), 1)
        self.assertEqual(voices[0]["voice_name"], "Expressive Narrator")
        self.assertEqual(voices[0]["description"], "English narrator")

    def test_async_inline_text_uses_async_audio_field(self) -> None:
        task = self.service.start_async_synthesis(make_request(text="Long hello."))

        self.assertEqual(task.task_id, "321")
        self.assertIsNone(self.minimax.uploaded_text)
        self.assertEqual(self.minimax.async_payload["text"], "Long hello.")  # type: ignore[index]
        self.assertEqual(
            self.minimax.async_payload["audio_setting"],  # type: ignore[index]
            {"audio_sample_rate": 16000, "format": "wav", "channel": 1},
        )
        self.assertNotIn("stream", self.minimax.async_payload)  # type: ignore[operator]

    def test_async_rejects_segmented_emotions(self) -> None:
        with self.assertRaisesRegex(ValidationError, "Long Text"):
            self.service.start_async_synthesis(
                make_request(
                    text="Hello. Goodbye.",
                    segments=[
                        {"text": "Hello. ", "emotion": "happy"},
                        {"text": "Goodbye.", "emotion": "sad"},
                    ],
                )
            )

    def test_async_large_text_uploads_utf8_file(self) -> None:
        text = "a" * 50001
        self.service.start_async_synthesis(make_request(text=text))

        self.assertEqual(self.minimax.uploaded_text, text)
        self.assertEqual(self.minimax.async_payload["text_file_id"], 123)  # type: ignore[index]
        self.assertNotIn("text", self.minimax.async_payload)  # type: ignore[operator]

    def test_async_success_downloads_and_validates_wav(self) -> None:
        self.minimax.async_query_response = {
            "status": "Success",
            "task_id": 321,
            "file_id": 456,
        }

        result = self.service.get_async_result("321")

        self.assertEqual(result.status, "success")
        self.assertIsNotNone(result.generated_audio)
        self.assertEqual(result.generated_audio.wav_info.sample_rate, 16000)  # type: ignore[union-attr]
        self.assertEqual(result.generated_audio.wav_info.channels, 1)  # type: ignore[union-attr]

    def test_async_rejects_more_than_200000_characters(self) -> None:
        with self.assertRaisesRegex(ValidationError, "200,000"):
            self.service.start_async_synthesis(
                make_request(text="a" * 200001)
            )


def demo_tests() -> None:
    unittest.main(module=__name__, verbosity=2)


def main() -> None:
    demo_tests()


if __name__ == "__main__":
    main()
