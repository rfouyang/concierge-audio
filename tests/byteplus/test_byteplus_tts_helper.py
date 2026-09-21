from __future__ import annotations

import base64
import json
import unittest
from unittest.mock import Mock

from component.byteplus.models import ByteplusApiError
from component.common.models import ConfigurationError
from util.byteplus_tts_helper import ByteplusTtsHelper


class ByteplusTtsHelperTests(unittest.TestCase):
    def make_helper(self, session: Mock, *, api_key: str = "test-key") -> ByteplusTtsHelper:
        return ByteplusTtsHelper(
            api_key=api_key,
            base_url="https://voice.ap-southeast-1.bytepluses.com",
            resource_id="seed-tts-2.0",
            user_id="test",
            connect_timeout_seconds=5,
            read_timeout_seconds=60,
            session=session,
        )

    def test_decodes_fragmented_stream_and_builds_context_payload(self) -> None:
        pcm = b"\x01\x02" * 32
        stream = (
            json.dumps({"code": 0, "message": "", "data": base64.b64encode(pcm).decode()})
            + json.dumps({"code": 0, "data": None, "sentence": {"text": "你好", "words": [], "phonemes": []}})
            + json.dumps({"code": 20000000, "message": "ok", "data": None})
        ).encode()
        response = Mock(status_code=200)
        response.iter_content.return_value = [stream[:17], stream[17:53], stream[53:]]
        session = Mock()
        session.post.return_value = response

        result = self.make_helper(session).synthesize(
            text="你好",
            voice_id="zh_female_vv_uranus_bigtts",
            sample_rate=16000,
            speech_rate=0,
            loudness_rate=0,
            context_text="用温柔的语气说。",
        )

        self.assertEqual(result.pcm, pcm)
        request = session.post.call_args
        self.assertEqual(request.kwargs["headers"]["X-Api-Key"], "test-key")
        self.assertEqual(request.kwargs["headers"]["X-Api-Resource-Id"], "seed-tts-2.0")
        audio_params = request.kwargs["json"]["req_params"]["audio_params"]
        self.assertEqual(audio_params["format"], "pcm")
        self.assertEqual(audio_params["sample_rate"], 16000)
        additions = json.loads(request.kwargs["json"]["req_params"]["additions"])
        self.assertEqual(additions["context_texts"], ["用温柔的语气说。"]) 
        self.assertEqual(request.kwargs["json"]["req_params"]["text"], "你好")

    def test_missing_key_fails_before_network(self) -> None:
        session = Mock()
        with self.assertRaises(ConfigurationError):
            self.make_helper(session, api_key="").synthesize(
                text="hello",
                voice_id="voice",
                sample_rate=16000,
                speech_rate=0,
                loudness_rate=0,
                context_text=None,
            )
        session.post.assert_not_called()

    def test_maps_voice_permission_error(self) -> None:
        response = Mock(status_code=200)
        response.iter_content.return_value = [
            json.dumps(
                {"code": 45000000, "message": "speaker permission denied", "data": None}
            ).encode()
        ]
        session = Mock()
        session.post.return_value = response
        with self.assertRaisesRegex(ByteplusApiError, "音色不可用"):
            self.make_helper(session).synthesize(
                text="hello",
                voice_id="voice",
                sample_rate=16000,
                speech_rate=0,
                loudness_rate=0,
                context_text=None,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
