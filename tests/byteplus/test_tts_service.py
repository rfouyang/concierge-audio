from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from typing import Any

from component.byteplus.models import ByteplusTtsRequest
from component.byteplus.tts_service import ByteplusTtsService
from component.common.models import ValidationError
from component.common.tts_history import TtsHistory
from component.byteplus.presets import list_presets
from config.byteplus_config import DEFAULT_PRESET_ID
from util.byteplus_tts_helper import ByteplusSynthesisResponse
from util.wav_helper import WavHelper


class FakeByteplusHelper:
    is_configured = True

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def synthesize(self, **values: Any) -> ByteplusSynthesisResponse:
        self.calls.append(values)
        return ByteplusSynthesisResponse(
            pcm=b"\x00\x00" * 1600,
            request_id=f"request-{len(self.calls)}",
        )


def make_request(**overrides: Any) -> ByteplusTtsRequest:
    values: dict[str, Any] = {
        "text": "欢迎使用 BytePlus。",
        "voice_id": "zh_female_vv_uranus_bigtts",
        "speech_rate": 0,
        "loudness_rate": 0,
    }
    values.update(overrides)
    return ByteplusTtsRequest.from_mapping(values)


class ByteplusTtsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.helper = FakeByteplusHelper()
        self.service = ByteplusTtsService(
            byteplus_helper=self.helper,  # type: ignore[arg-type]
            wav_helper=WavHelper(required_sample_rate=16000, required_channels=1),
            max_segments=50,
        )

    def test_plain_text_requests_16k_pcm_and_returns_wav(self) -> None:
        generated = self.service.synthesize(make_request())
        self.assertEqual(generated.wav_info.sample_rate, 16000)
        self.assertEqual(generated.wav_info.channels, 1)
        self.assertEqual(self.helper.calls[0]["sample_rate"], 16000)
        self.assertIsNone(self.helper.calls[0]["context_text"])
        self.assertIsNone(generated.synthesis_details["segments"][0]["context_text"])
        self.assertEqual(generated.synthesis_details["segments"][0]["text"], "欢迎使用 BytePlus。")

    def test_segment_styles_use_clean_text_and_distinct_prompts(self) -> None:
        generated = self.service.synthesize(
            make_request(
                text="你好。请跟我来。",
                segments=[
                    {
                        "text": "你好。",
                        "style": {
                            "emotion": "happy",
                            "social_tone": "warm",
                            "communicative_intent": "invite",
                        },
                    },
                    {
                        "text": "请跟我来。",
                        "style": {
                            "emotion": "neutral",
                            "social_tone": "professional",
                            "communicative_intent": "inform",
                        },
                    },
                ],
            )
        )
        self.assertEqual([call["text"] for call in self.helper.calls], ["你好。", "请跟我来。"]) 
        self.assertIn("开心", self.helper.calls[0]["context_text"])
        self.assertIn("专业", self.helper.calls[1]["context_text"])
        self.assertNotIn("happy", str([call["text"] for call in self.helper.calls]))
        self.assertAlmostEqual(generated.wav_info.duration_seconds, 0.2)

    def test_adjacent_equal_styles_are_merged(self) -> None:
        style = {"emotion": "happy"}
        self.service.synthesize(
            make_request(
                text="你好世界",
                segments=[
                    {"text": "你好", "style": style},
                    {"text": "世界", "style": style},
                ],
            )
        )
        self.assertEqual(len(self.helper.calls), 1)
        self.assertEqual(self.helper.calls[0]["text"], "你好世界")

    def test_history_retains_actual_prompt_without_credentials(self) -> None:
        request = make_request(segments=[{
            "text": "欢迎使用 BytePlus。", "style": {"preset_id": "064", "voice_texture": ["whispering"]},
        }])
        generated = self.service.synthesize(request)
        with tempfile.TemporaryDirectory() as directory:
            history = TtsHistory(Path(directory))
            history.save("byteplus", generated, {"text": request.text, "voice_id": request.voice_id, "api_key": "never-save"})
            record = history.list("byteplus")[0]
            details = record["synthesis_details"]["segments"][0]
            self.assertEqual(details["context_text"], self.helper.calls[0]["context_text"])
            self.assertEqual(details["request_id"], "request-1")
            self.assertNotIn("never-save", str(record))

    def test_preset_scene_prompt_is_separate_from_spoken_text(self) -> None:
        preset = next(p for p in list_presets() if p["id"] == DEFAULT_PRESET_ID)
        self.service.synthesize(make_request(
            text="你好。",
            segments=[{"text": "你好。", "style": {
                **preset["style"], "preset_id": preset["id"], "pace": "slow",
            }}],
        ))
        self.assertEqual(self.helper.calls[0]["text"], "你好。")
        self.assertIn(preset["scene_prompt"], self.helper.calls[0]["context_text"])
        self.assertIn("语速较慢", self.helper.calls[0]["context_text"])

    def test_rejects_mismatched_segments(self) -> None:
        with self.assertRaisesRegex(ValidationError, "完全一致"):
            self.service.synthesize(
                make_request(text="你好", segments=[{"text": "再见", "style": None}])
            )

    def test_official_catalog_contains_chinese_and_english_voices(self) -> None:
        voices = self.service.list_voices()
        self.assertEqual(len(voices), 151)
        self.assertEqual(sum(v["language"] == "Chinese" for v in voices), 23)
        self.assertEqual(sum(v["language"] == "English" for v in voices), 54)


if __name__ == "__main__":
    unittest.main(verbosity=2)
