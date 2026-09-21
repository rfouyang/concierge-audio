from __future__ import annotations

import unittest

from component.byteplus.models import ByteplusStyleConfig
from component.byteplus.presets import list_presets
from component.byteplus.prompt_mapper import build_byteplus_prompt, normalize_style
from component.common.models import ValidationError
from config.byteplus_config import DEFAULT_PRESET_ID


class ByteplusPromptMapperTests(unittest.TestCase):
    def test_default_preset_is_reception_introduction(self) -> None:
        preset = next(p for p in list_presets() if p["id"] == DEFAULT_PRESET_ID)
        self.assertEqual(
            (preset["category"], preset["subcategory"], preset["name"]),
            ("接待服务", "身份介绍", "自我介绍"),
        )

    def test_unknown_preset_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            build_byteplus_prompt(ByteplusStyleConfig.from_mapping({"preset_id": "unknown"}))

    def test_builds_reference_special_prompt(self) -> None:
        style = ByteplusStyleConfig.from_mapping(
            {
                "emotion": "sad",
                "intensity": "moderate",
                "social_tone": "gentle",
                "mental_state": ["hurt", "restrained"],
                "communicative_intent": "reassure",
                "voice_texture": ["soft", "trembling"],
                "pace": "slow",
                "pitch": "slightly_low",
                "energy": "low",
            }
        )
        prompt = build_byteplus_prompt(style)
        self.assertIn("悲伤但克制", prompt)
        self.assertIn("让对方安心", prompt)
        self.assertIn("语速较慢", prompt)
        self.assertNotIn("不要过度夸张", prompt)
        self.assertIn("充分表现", prompt)

    def test_normalizes_conflicting_intimate_powerful_texture(self) -> None:
        style = ByteplusStyleConfig.from_mapping(
            {"social_tone": "intimate", "voice_texture": ["powerful"]}
        )
        normalized = normalize_style(style)
        self.assertEqual(normalized.voice_texture, ("soft",))

    def test_all_supplied_presets_map_to_valid_prompts(self) -> None:
        presets = list_presets()
        self.assertEqual(len(presets), 150)
        self.assertEqual(len({p["id"] for p in presets}), 150)
        for preset in presets:
            self.assertEqual(len(preset["category"]), 4)
            self.assertEqual(len(preset["subcategory"]), 4)
            style = ByteplusStyleConfig.from_mapping(preset["style"])
            directed = ByteplusStyleConfig.from_mapping({**preset["style"], "preset_id": preset["id"]})
            self.assertIn(preset["scene_prompt"], build_byteplus_prompt(directed))
            self.assertTrue(build_byteplus_prompt(style))


if __name__ == "__main__":
    unittest.main(verbosity=2)
