"""HTTP adapter for BytePlus Seed Speech unidirectional streaming TTS."""

from __future__ import annotations

import base64
import binascii
import codecs
import json
import uuid
from dataclasses import dataclass
from typing import Any, Iterator, Mapping

import requests

from component.byteplus.models import ByteplusApiError
from component.common.models import ConfigurationError


@dataclass(frozen=True, slots=True)
class ByteplusSynthesisResponse:
    pcm: bytes
    request_id: str


class ByteplusTtsHelper:
    ENDPOINT_PATH = "/api/v3/tts/unidirectional"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        resource_id: str,
        user_id: str,
        connect_timeout_seconds: float,
        read_timeout_seconds: float,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.resource_id = resource_id
        self.user_id = user_id
        self.connect_timeout_seconds = connect_timeout_seconds
        self.read_timeout_seconds = read_timeout_seconds
        self.session = session or requests.Session()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def synthesize(
        self,
        *,
        text: str,
        voice_id: str,
        sample_rate: int,
        speech_rate: int,
        loudness_rate: int,
        context_text: str | None,
    ) -> ByteplusSynthesisResponse:
        self._require_api_key()
        request_id = str(uuid.uuid4())
        additions: dict[str, Any] = {
            "disable_markdown_filter": True,
            "disable_emoji_filter": True,
        }
        if context_text:
            additions["context_texts"] = [context_text]
        payload = {
            "user": {"uid": self.user_id},
            "req_params": {
                "text": text,
                "speaker": voice_id,
                "audio_params": {
                    "format": "pcm",
                    "sample_rate": sample_rate,
                    "speech_rate": speech_rate,
                    "loudness_rate": loudness_rate,
                },
                "additions": json.dumps(additions, ensure_ascii=False),
            },
        }
        headers = {
            "X-Api-Key": self.api_key,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Request-Id": request_id,
            "Content-Type": "application/json",
            "Connection": "keep-alive",
        }
        try:
            response = self.session.post(
                f"{self.base_url}{self.ENDPOINT_PATH}",
                headers=headers,
                json=payload,
                stream=True,
                timeout=(self.connect_timeout_seconds, self.read_timeout_seconds),
            )
        except requests.Timeout as error:
            raise ByteplusApiError(
                "BytePlus 请求超时，请稍后重试。",
                request_id=request_id,
            ) from error
        except requests.RequestException as error:
            raise ByteplusApiError(
                "无法连接 BytePlus 语音服务。",
                request_id=request_id,
            ) from error

        if response.status_code >= 400:
            raise ByteplusApiError(
                f"BytePlus HTTP 请求失败：{response.status_code}。",
                status_code=response.status_code,
                request_id=request_id,
            )

        audio_parts: list[bytes] = []
        completed = False
        for message in self._iter_json_messages(response):
            code = message.get("code")
            if code == 0:
                encoded_audio = message.get("data")
                # Successful sentence metadata accompanies the audio chunks.
                if encoded_audio is None and isinstance(message.get("sentence"), Mapping):
                    continue
                if not isinstance(encoded_audio, str):
                    raise ByteplusApiError(
                        "BytePlus 音频响应缺少 Base64 数据。",
                        request_id=request_id,
                    )
                try:
                    audio_parts.append(base64.b64decode(encoded_audio, validate=True))
                except (ValueError, binascii.Error) as error:
                    raise ByteplusApiError(
                        "BytePlus 返回了无效的 Base64 音频。",
                        request_id=request_id,
                    ) from error
            elif code == 20000000:
                completed = True
            else:
                message_text = message.get("message")
                raise ByteplusApiError(
                    _friendly_error_message(code, message_text),
                    status_code=code if isinstance(code, int) else None,
                    request_id=request_id,
                )
        if not completed:
            raise ByteplusApiError(
                "BytePlus 流式响应未正常结束。",
                request_id=request_id,
            )
        pcm = b"".join(audio_parts)
        if not pcm:
            raise ByteplusApiError(
                "BytePlus 没有返回音频数据。",
                request_id=request_id,
            )
        return ByteplusSynthesisResponse(pcm=pcm, request_id=request_id)

    @staticmethod
    def _iter_json_messages(response: requests.Response) -> Iterator[Mapping[str, Any]]:
        decoder = json.JSONDecoder()
        utf8_decoder = codecs.getincrementaldecoder("utf-8")()
        buffer = ""
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            buffer += utf8_decoder.decode(chunk)
            messages, buffer = _decode_available(buffer, decoder)
            yield from messages
        buffer += utf8_decoder.decode(b"", final=True)
        messages, buffer = _decode_available(buffer, decoder)
        yield from messages
        if buffer.strip():
            raise ByteplusApiError("BytePlus 返回了不完整的 JSON 数据。")

    def _require_api_key(self) -> None:
        if not self.api_key:
            raise ConfigurationError(
                "尚未配置 BYTEPLUS_API_KEY，请先在 .env 中填写。"
            )


def _decode_available(
    buffer: str,
    decoder: json.JSONDecoder,
) -> tuple[list[Mapping[str, Any]], str]:
    messages: list[Mapping[str, Any]] = []
    while True:
        buffer = buffer.lstrip()
        if not buffer:
            return messages, ""
        if buffer.startswith("data:"):
            buffer = buffer[5:].lstrip()
        try:
            value, end = decoder.raw_decode(buffer)
        except json.JSONDecodeError:
            return messages, buffer
        if not isinstance(value, Mapping):
            raise ByteplusApiError("BytePlus 流中包含非对象 JSON 数据。")
        messages.append(value)
        buffer = buffer[end:]


def _friendly_error_message(code: Any, message: Any) -> str:
    if code == 40402003:
        return "BytePlus 文本长度超过限制。"
    if code == 45000000:
        return "BytePlus 音色不可用或当前账号没有该音色权限。"
    if code == 55000000:
        return "BytePlus 服务错误，请检查音色与 Resource ID 是否匹配。"
    detail = message if isinstance(message, str) and message else "未知错误"
    return f"BytePlus 合成失败：{detail}。"
