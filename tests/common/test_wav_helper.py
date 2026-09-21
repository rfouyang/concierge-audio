from __future__ import annotations

import unittest

from component.common.models import AudioValidationError
from tests.minimax.test_tts_service import make_wav
from util.wav_helper import WavHelper


class WavHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.helper = WavHelper(required_sample_rate=16000, required_channels=1)

    def test_accepts_16k_mono_wav(self) -> None:
        info = self.helper.inspect(make_wav())
        self.assertEqual(info.sample_rate, 16000)
        self.assertEqual(info.channels, 1)
        self.assertGreater(info.duration_seconds, 0)

    def test_rejects_wrong_sample_rate(self) -> None:
        with self.assertRaisesRegex(AudioValidationError, "不是 G1 要求"):
            self.helper.inspect(make_wav(sample_rate=32000))

    def test_rejects_stereo(self) -> None:
        with self.assertRaisesRegex(AudioValidationError, "声道数"):
            self.helper.inspect(make_wav(channels=2))

    def test_rejects_invalid_wav(self) -> None:
        with self.assertRaisesRegex(AudioValidationError, "有效的 WAV"):
            self.helper.inspect(b"not-a-wav")

    def test_concatenates_verified_wav_segments(self) -> None:
        combined = self.helper.concatenate([make_wav(), make_wav()])
        info = self.helper.inspect(combined)
        self.assertAlmostEqual(info.duration_seconds, 0.2)

    def test_wraps_raw_pcm_as_g1_wav(self) -> None:
        audio = self.helper.from_pcm(b"\x00\x00" * 1600)
        info = self.helper.inspect(audio)
        self.assertEqual(info.sample_rate, 16000)
        self.assertEqual(info.channels, 1)
        self.assertEqual(info.sample_width_bytes, 2)
        self.assertAlmostEqual(info.duration_seconds, 0.1)

    def test_rejects_incompatible_wav_segments(self) -> None:
        with self.assertRaisesRegex(AudioValidationError, "不是 G1 要求"):
            self.helper.concatenate([make_wav(), make_wav(sample_rate=32000)])


def demo_tests() -> None:
    unittest.main(module=__name__, verbosity=2)


def main() -> None:
    demo_tests()


if __name__ == "__main__":
    main()
