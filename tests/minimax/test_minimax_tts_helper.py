from __future__ import annotations

import io
import tarfile
import unittest
from unittest.mock import Mock

import requests

from component.common.models import ConfigurationError
from component.minimax.models import MinimaxApiError
from util.minimax_tts_helper import MinimaxTtsHelper


class MinimaxTtsHelperTests(unittest.TestCase):
    def make_helper(self, session: Mock, *, api_key: str = "test-key") -> MinimaxTtsHelper:
        return MinimaxTtsHelper(
            api_key=api_key,
            base_url="https://api.minimax.io",
            connect_timeout_seconds=5,
            read_timeout_seconds=60,
            session=session,
        )

    def test_decodes_hex_audio(self) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": {"audio": "52494646", "status": 2},
            "trace_id": "trace-1",
            "extra_info": {},
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }
        session = Mock()
        session.post.return_value = response

        result = self.make_helper(session).synthesize({"text": "hello"})

        self.assertEqual(result.audio, b"RIFF")
        self.assertEqual(result.trace_id, "trace-1")
        request_headers = session.post.call_args.kwargs["headers"]
        self.assertEqual(request_headers["Authorization"], "Bearer test-key")

    def test_missing_key_fails_before_network(self) -> None:
        session = Mock()
        with self.assertRaises(ConfigurationError):
            self.make_helper(session, api_key="").get_voices()
        session.post.assert_not_called()

    def test_rejects_incomplete_synthesis(self) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": {"audio": "52494646", "status": 1},
            "trace_id": "trace-incomplete",
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }
        session = Mock()
        session.post.return_value = response

        with self.assertRaisesRegex(MinimaxApiError, "尚未完成"):
            self.make_helper(session).synthesize({"text": "hello"})

    def test_maps_authentication_failure(self) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "base_resp": {"status_code": 1004, "status_msg": "invalid token"}
        }
        session = Mock()
        session.post.return_value = response

        with self.assertRaisesRegex(MinimaxApiError, "API Key"):
            self.make_helper(session).get_voices()

    def test_maps_timeout(self) -> None:
        session = Mock()
        session.post.side_effect = requests.Timeout()
        with self.assertRaisesRegex(MinimaxApiError, "超时"):
            self.make_helper(session).get_voices()

    def test_uploads_async_text_with_required_purpose(self) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "file": {"file_id": 123},
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }
        session = Mock()
        session.post.return_value = response

        file_id = self.make_helper(session).upload_async_text("hello")

        self.assertEqual(file_id, 123)
        request = session.post.call_args
        self.assertEqual(request.kwargs["data"], {"purpose": "t2a_async_input"})
        self.assertEqual(request.kwargs["files"]["file"][1], b"hello")

    def test_queries_async_task_with_task_id(self) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "task_id": 321,
            "status": "Processing",
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }
        session = Mock()
        session.get.return_value = response

        result = self.make_helper(session).query_async_task("321")

        self.assertEqual(result["status"], "Processing")
        self.assertEqual(session.get.call_args.kwargs["params"], {"task_id": "321"})

    def test_downloads_async_audio_content(self) -> None:
        response = Mock()
        response.status_code = 200
        response.content = b"RIFF-test"
        session = Mock()
        session.get.return_value = response

        audio = self.make_helper(session).download_file(456)

        self.assertEqual(audio, b"RIFF-test")
        self.assertEqual(session.get.call_args.kwargs["params"], {"file_id": 456})

    def test_extracts_single_wav_from_async_tar(self) -> None:
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as archive:
            wav = b"RIFF-async-test"
            wav_info = tarfile.TarInfo("result/audio.wav")
            wav_info.size = len(wav)
            archive.addfile(wav_info, io.BytesIO(wav))
            metadata = b"{}"
            metadata_info = tarfile.TarInfo("result/audio.extra")
            metadata_info.size = len(metadata)
            archive.addfile(metadata_info, io.BytesIO(metadata))

        response = Mock()
        response.status_code = 200
        response.content = tar_buffer.getvalue()
        session = Mock()
        session.get.return_value = response

        audio = self.make_helper(session).download_async_audio(456)

        self.assertEqual(audio, b"RIFF-async-test")


def demo_tests() -> None:
    unittest.main(module=__name__, verbosity=2)


def main() -> None:
    demo_tests()


if __name__ == "__main__":
    main()
