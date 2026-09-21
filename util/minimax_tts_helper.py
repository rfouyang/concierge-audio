"""Low-level HTTP adapter for MiniMax speech APIs."""

from __future__ import annotations

import io
import tarfile
from dataclasses import dataclass
from typing import Any, Mapping

import requests

from component.common.models import ConfigurationError
from component.minimax.models import MinimaxApiError


@dataclass(frozen=True, slots=True)
class MinimaxSynthesisResponse:
    """Decoded response fields needed by the business layer."""

    audio: bytes
    trace_id: str
    extra_info: Mapping[str, Any]


class MinimaxTtsHelper:
    """Perform authenticated MiniMax API operations."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        connect_timeout_seconds: float,
        read_timeout_seconds: float,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = (connect_timeout_seconds, read_timeout_seconds)
        self.session = session or requests.Session()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def synthesize(self, payload: Mapping[str, Any]) -> MinimaxSynthesisResponse:
        """Generate speech and decode MiniMax's hex audio payload."""

        response_data = self._post_json("/v1/t2a_v2", payload)
        data = response_data.get("data")
        if not isinstance(data, Mapping):
            raise MinimaxApiError(
                "MiniMax 返回了空的音频数据。",
                trace_id=_optional_text(response_data.get("trace_id")),
            )

        stream_status = data.get("status")
        if isinstance(stream_status, int) and stream_status != 2:
            raise MinimaxApiError(
                "MiniMax 音频尚未完成合成。",
                trace_id=_optional_text(response_data.get("trace_id")),
            )

        encoded_audio = data.get("audio")
        if not isinstance(encoded_audio, str) or not encoded_audio:
            raise MinimaxApiError(
                "MiniMax 响应中没有可用的音频。",
                trace_id=_optional_text(response_data.get("trace_id")),
            )

        try:
            audio = bytes.fromhex(encoded_audio)
        except ValueError as error:
            raise MinimaxApiError(
                "MiniMax 返回的音频编码无效。",
                trace_id=_optional_text(response_data.get("trace_id")),
            ) from error

        extra_info = response_data.get("extra_info")
        return MinimaxSynthesisResponse(
            audio=audio,
            trace_id=_optional_text(response_data.get("trace_id")) or "",
            extra_info=extra_info if isinstance(extra_info, Mapping) else {},
        )

    def get_voices(self) -> Mapping[str, Any]:
        """Return voices available to the configured MiniMax account."""

        return self._post_json("/v1/get_voice", {"voice_type": "all"})

    def upload_async_text(self, text: str) -> int:
        """Upload UTF-8 text for an asynchronous long-TTS task."""

        self._require_api_key()
        try:
            response = self.session.post(
                f"{self.base_url}/v1/files/upload",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"purpose": "t2a_async_input"},
                files={"file": ("concierge_long_text.txt", text.encode("utf-8"), "text/plain")},
                timeout=self.timeout,
            )
        except requests.Timeout as error:
            raise MinimaxApiError("MiniMax 文本上传超时，请稍后重试。") from error
        except requests.RequestException as error:
            raise MinimaxApiError("无法连接 MiniMax 服务。") from error

        response_data = self._parse_json_response(response)
        file_data = response_data.get("file")
        file_id = file_data.get("file_id") if isinstance(file_data, Mapping) else None
        if not isinstance(file_id, int):
            raise MinimaxApiError("MiniMax 文本上传响应中没有 file_id。")
        return file_id

    def create_async_task(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Create an asynchronous long-TTS task."""

        return self._post_json("/v1/t2a_async_v2", payload)

    def query_async_task(self, task_id: str) -> Mapping[str, Any]:
        """Read the latest state for one asynchronous task."""

        return self._get_json(
            "/v1/query/t2a_async_query_v2",
            params={"task_id": task_id},
        )

    def download_file(self, file_id: int) -> bytes:
        """Download generated file bytes from MiniMax file storage."""

        self._require_api_key()
        try:
            response = self.session.get(
                f"{self.base_url}/v1/files/retrieve_content",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"file_id": file_id},
                timeout=self.timeout,
            )
        except requests.Timeout as error:
            raise MinimaxApiError("MiniMax 音频下载超时，请稍后重试。") from error
        except requests.RequestException as error:
            raise MinimaxApiError("无法连接 MiniMax 服务。") from error

        if response.status_code >= 400:
            try:
                self._raise_for_response_data(response.json(), response.status_code)
            except ValueError as error:
                raise MinimaxApiError(
                    f"MiniMax 音频下载失败（HTTP {response.status_code}）。"
                ) from error
        if not response.content:
            raise MinimaxApiError("MiniMax 返回的异步音频为空。")
        return response.content

    def download_async_audio(self, file_id: int) -> bytes:
        """Download and unwrap the single WAV in an Async TTS result."""

        content = self.download_file(file_id)
        if content.startswith(b"RIFF"):
            return content
        try:
            with tarfile.open(fileobj=io.BytesIO(content), mode="r:*") as archive:
                wav_members = [
                    member
                    for member in archive.getmembers()
                    if member.isfile() and member.name.lower().endswith(".wav")
                ]
                if len(wav_members) != 1:
                    raise MinimaxApiError(
                        "MiniMax 异步结果中没有唯一的 WAV 文件。"
                    )
                extracted = archive.extractfile(wav_members[0])
                if extracted is None:
                    raise MinimaxApiError("无法读取 MiniMax 异步 WAV 文件。")
                audio = extracted.read()
        except tarfile.TarError as error:
            raise MinimaxApiError("MiniMax 异步结果不是有效的 TAR 文件。") from error
        if not audio:
            raise MinimaxApiError("MiniMax 异步 WAV 文件为空。")
        return audio

    def _post_json(
        self,
        path: str,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        self._require_api_key()

        try:
            response = self.session.post(
                f"{self.base_url}{path}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=dict(payload),
                timeout=self.timeout,
            )
        except requests.Timeout as error:
            raise MinimaxApiError("MiniMax 请求超时，请稍后重试。") from error
        except requests.RequestException as error:
            raise MinimaxApiError("无法连接 MiniMax 服务。") from error

        return self._parse_json_response(response)

    def _get_json(
        self,
        path: str,
        *,
        params: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        self._require_api_key()
        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params=dict(params),
                timeout=self.timeout,
            )
        except requests.Timeout as error:
            raise MinimaxApiError("MiniMax 请求超时，请稍后重试。") from error
        except requests.RequestException as error:
            raise MinimaxApiError("无法连接 MiniMax 服务。") from error
        return self._parse_json_response(response)

    def _parse_json_response(self, response: requests.Response) -> Mapping[str, Any]:
        try:
            response_data = response.json()
        except ValueError as error:
            raise MinimaxApiError(
                f"MiniMax 返回了无法解析的响应（HTTP {response.status_code}）。"
            ) from error
        if not isinstance(response_data, Mapping):
            raise MinimaxApiError("MiniMax 返回了格式异常的响应。")
        self._raise_for_response_data(response_data, response.status_code)
        return response_data

    def _raise_for_response_data(
        self,
        response_data: Mapping[str, Any],
        http_status_code: int,
    ) -> None:
        trace_id = _optional_text(response_data.get("trace_id"))
        base_response = response_data.get("base_resp")
        api_status_code: int | None = None
        api_status_message = ""
        if isinstance(base_response, Mapping):
            raw_status_code = base_response.get("status_code")
            if isinstance(raw_status_code, int):
                api_status_code = raw_status_code
            api_status_message = _optional_text(base_response.get("status_msg")) or ""

        if http_status_code >= 400 or api_status_code not in {None, 0}:
            message = _friendly_error_message(
                api_status_code,
                api_status_message,
                http_status_code,
            )
            raise MinimaxApiError(
                message,
                status_code=api_status_code or http_status_code,
                trace_id=trace_id,
            )

    def _require_api_key(self) -> None:
        if not self.api_key:
            raise ConfigurationError(
                "尚未配置 MINIMAX_API_KEY，请先在 .env 中填写 MiniMax API Key。"
            )


def _friendly_error_message(
    api_status_code: int | None,
    api_status_message: str,
    http_status_code: int,
) -> str:
    known_messages = {
        1001: "MiniMax 请求超时，请稍后重试。",
        1002: "MiniMax 请求过于频繁，请稍后重试。",
        1004: "MiniMax API Key 无效或没有权限。",
        1039: "MiniMax TPM 配额已达到限制。",
        1042: "文本中的无效字符比例超过限制。",
        2013: "MiniMax 拒绝了请求参数，请检查模型和音色配置。",
    }
    if api_status_code in known_messages:
        return known_messages[api_status_code]
    if api_status_message:
        return f"MiniMax 请求失败：{api_status_message}"
    return f"MiniMax 请求失败（HTTP {http_status_code}）。"


def _optional_text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def demo_minimax_tts_helper() -> None:
    helper = MinimaxTtsHelper(
        api_key="",
        base_url="https://api.minimax.io",
        connect_timeout_seconds=10,
        read_timeout_seconds=120,
    )
    print({"configured": helper.is_configured, "base_url": helper.base_url})


def main() -> None:
    demo_minimax_tts_helper()


if __name__ == "__main__":
    main()
