"""Thin Flask routes for MiniMax text-to-speech operations."""

from __future__ import annotations

import logging
from datetime import datetime

from flask import Blueprint, Response, jsonify, request

from component.common.models import (
    AudioValidationError,
    ConfigurationError,
    GeneratedAudio,
    ValidationError,
)
from component.minimax.models import MinimaxApiError, MinimaxTtsRequest
from component.minimax.tts_service import MinimaxTtsService


LOGGER = logging.getLogger(__name__)
from app.api_tts.routes.api_history import history_store


def create_minimax_api_blueprint(tts_service: MinimaxTtsService) -> Blueprint:
    blueprint = Blueprint("minimax_api", __name__)

    @blueprint.get("/health")
    def health() -> tuple[Response, int]:
        status_code = 200 if tts_service.is_configured else 503
        return (
            jsonify(
                {
                    "status": "ready" if tts_service.is_configured else "not_configured",
                    "minimax_configured": tts_service.is_configured,
                    "audio": {
                        "sample_rate": MinimaxTtsService.SAMPLE_RATE,
                        "channels": MinimaxTtsService.CHANNELS,
                        "format": MinimaxTtsService.AUDIO_FORMAT,
                    },
                }
            ),
            status_code,
        )

    @blueprint.get("/voices")
    def voices() -> tuple[Response, int] | Response:
        try:
            force_refresh = request.args.get("refresh") == "1"
            return jsonify(
                {
                    "voices": tts_service.list_voices(force_refresh=force_refresh),
                }
            )
        except ConfigurationError as error:
            return _error_response(str(error), 503)
        except MinimaxApiError as error:
            return _minimax_error_response(error)

    @blueprint.post("/tts")
    def synthesize() -> tuple[Response, int] | Response:
        request_data = request.get_json(silent=True)
        if not isinstance(request_data, dict):
            return _error_response("请求体必须是 JSON 对象。", 400)

        try:
            synthesis_request = MinimaxTtsRequest.from_mapping(request_data)
            generated_audio = tts_service.synthesize(synthesis_request)
            history_store().save("minimax", generated_audio, request_data)
        except ValidationError as error:
            return _error_response(str(error), 400)
        except ConfigurationError as error:
            return _error_response(str(error), 503)
        except MinimaxApiError as error:
            return _minimax_error_response(error)
        except AudioValidationError as error:
            LOGGER.error("Generated audio failed G1 validation: %s", error)
            return _error_response(str(error), 502)
        except Exception:
            LOGGER.exception("Unexpected text-to-speech failure")
            return _error_response("生成语音时发生内部错误。", 500)

        return _audio_response(
            generated_audio,
            usage_characters=len(synthesis_request.text),
        )

    @blueprint.post("/tts/async")
    def create_async_synthesis() -> tuple[Response, int] | Response:
        request_data = request.get_json(silent=True)
        if not isinstance(request_data, dict):
            return _error_response("请求体必须是 JSON 对象。", 400)

        try:
            synthesis_request = MinimaxTtsRequest.from_mapping(request_data)
            task = tts_service.start_async_synthesis(synthesis_request)
            history_store().remember_task(task.task_id, request_data)
            return (
                jsonify(
                    {
                        "status": "processing",
                        "task_id": task.task_id,
                        "file_id": task.file_id,
                        "usage_characters": task.usage_characters,
                    }
                ),
                202,
            )
        except ValidationError as error:
            return _error_response(str(error), 400)
        except ConfigurationError as error:
            return _error_response(str(error), 503)
        except MinimaxApiError as error:
            return _minimax_error_response(error)
        except Exception:
            LOGGER.exception("Unexpected asynchronous text-to-speech failure")
            return _error_response("创建长文本语音任务时发生内部错误。", 500)

    @blueprint.get("/tts/async/<task_id>")
    def query_async_synthesis(task_id: str) -> tuple[Response, int] | Response:
        try:
            result = tts_service.get_async_result(task_id)
            if result.status == "processing":
                return (
                    jsonify(
                        {
                            "status": result.status,
                            "task_id": result.task_id,
                            "file_id": result.file_id,
                        }
                    ),
                    202,
                )
            if result.generated_audio is None:
                return _error_response("MiniMax 异步任务没有返回音频。", 502)
            history_store().save_task(task_id, result.generated_audio)
            return _audio_response(result.generated_audio, usage_characters=None)
        except ValidationError as error:
            return _error_response(str(error), 400)
        except ConfigurationError as error:
            return _error_response(str(error), 503)
        except MinimaxApiError as error:
            return _minimax_error_response(error)
        except AudioValidationError as error:
            LOGGER.error("Asynchronous audio failed G1 validation: %s", error)
            return _error_response(str(error), 502)
        except Exception:
            LOGGER.exception("Unexpected asynchronous task query failure")
            return _error_response("查询长文本语音任务时发生内部错误。", 500)

    return blueprint


def _minimax_error_response(error: MinimaxApiError) -> tuple[Response, int]:
    response_status = 502
    if error.status_code in {1002, 1039, 429}:
        response_status = 429
    elif error.status_code in {1004, 401, 403}:
        response_status = 401
    return _error_response(str(error), response_status, trace_id=error.trace_id)


def _audio_response(
    generated_audio: GeneratedAudio,
    *,
    usage_characters: int | None,
) -> Response:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response = Response(generated_audio.audio, mimetype="audio/wav")
    response.headers["Content-Disposition"] = (
        f'inline; filename="concierge_{timestamp}_16k.wav"'
    )
    response.headers["X-Audio-Sample-Rate"] = str(
        generated_audio.wav_info.sample_rate
    )
    response.headers["X-Audio-Channels"] = str(generated_audio.wav_info.channels)
    response.headers["X-Audio-Duration-Ms"] = str(
        round(generated_audio.wav_info.duration_seconds * 1000)
    )
    response.headers["X-Audio-Sample-Width"] = str(
        generated_audio.wav_info.sample_width_bytes
    )
    resolved_usage = generated_audio.usage_characters or usage_characters
    if resolved_usage is not None:
        response.headers["X-Usage-Characters"] = str(resolved_usage)
    if generated_audio.trace_id:
        response.headers["X-Minimax-Trace-Id"] = generated_audio.trace_id
    return response


def _error_response(
    message: str,
    status_code: int,
    *,
    trace_id: str | None = None,
) -> tuple[Response, int]:
    payload: dict[str, str] = {"error": message}
    if trace_id:
        payload["trace_id"] = trace_id
    return jsonify(payload), status_code


def demo_api_blueprint() -> None:
    print(
        {
            "routes": [
                "/api/minimax/health",
                "/api/minimax/voices",
                "/api/minimax/tts",
                "/api/minimax/tts/async",
                "/api/minimax/tts/async/<task_id>",
            ]
        }
    )


def main() -> None:
    demo_api_blueprint()


if __name__ == "__main__":
    main()
