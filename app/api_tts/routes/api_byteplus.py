"""Thin Flask routes for BytePlus Seed Speech operations."""

from __future__ import annotations

import logging
from datetime import datetime

from flask import Blueprint, Response, jsonify, request

from component.byteplus.models import (
    ByteplusApiError,
    ByteplusStyleConfig,
    ByteplusTtsRequest,
)
from component.byteplus.tts_service import ByteplusTtsService
from component.common.models import (
    AudioValidationError,
    ConfigurationError,
    GeneratedAudio,
    ValidationError,
)


LOGGER = logging.getLogger(__name__)
from app.api_tts.routes.api_history import history_store
from config.byteplus_config import DEFAULT_PRESET_ID


def create_byteplus_api_blueprint(
    tts_service: ByteplusTtsService,
) -> Blueprint:
    blueprint = Blueprint("byteplus_api", __name__)

    @blueprint.get("/health")
    def health() -> tuple[Response, int]:
        status_code = 200 if tts_service.is_configured else 503
        return (
            jsonify(
                {
                    "status": "ready" if tts_service.is_configured else "not_configured",
                    "byteplus_configured": tts_service.is_configured,
                    "audio": {
                        "sample_rate": tts_service.SAMPLE_RATE,
                        "channels": tts_service.CHANNELS,
                        "format": tts_service.AUDIO_FORMAT,
                    },
                }
            ),
            status_code,
        )

    @blueprint.get("/voices")
    def voices() -> Response:
        return jsonify({"voices": tts_service.list_voices()})

    @blueprint.get("/presets")
    def presets() -> Response:
        return jsonify({"presets": tts_service.list_presets(), "default_preset_id": DEFAULT_PRESET_ID})

    @blueprint.post("/prompt-preview")
    def prompt_preview() -> tuple[Response, int] | Response:
        values = request.get_json(silent=True)
        if not isinstance(values, dict):
            return _error_response("请求体必须是 JSON 对象。", 400)
        try:
            style_values = values.get("style", values)
            if not isinstance(style_values, dict):
                raise ValidationError("style 必须是 JSON 对象。")
            style = ByteplusStyleConfig.from_mapping(style_values)
            return jsonify(
                {
                    "prompt": tts_service.preview_prompt(style),
                    "style": style.as_dict(),
                }
            )
        except ValidationError as error:
            return _error_response(str(error), 400)

    @blueprint.post("/tts")
    def synthesize() -> tuple[Response, int] | Response:
        values = request.get_json(silent=True)
        if not isinstance(values, dict):
            return _error_response("请求体必须是 JSON 对象。", 400)
        try:
            synthesis_request = ByteplusTtsRequest.from_mapping(values)
            generated_audio = tts_service.synthesize(synthesis_request)
            history_store().save("byteplus", generated_audio, values)
            return _audio_response(generated_audio)
        except ValidationError as error:
            return _error_response(str(error), 400)
        except ConfigurationError as error:
            return _error_response(str(error), 503)
        except ByteplusApiError as error:
            return _byteplus_error_response(error)
        except AudioValidationError as error:
            LOGGER.error("BytePlus audio failed G1 validation: %s", error)
            return _error_response(str(error), 502)
        except Exception:
            LOGGER.exception("Unexpected BytePlus text-to-speech failure")
            return _error_response("生成 BytePlus 语音时发生内部错误。", 500)

    return blueprint


def _byteplus_error_response(error: ByteplusApiError) -> tuple[Response, int]:
    status_code = 502
    if error.status_code in {401, 403, 45000000}:
        status_code = 401
    elif error.status_code == 429:
        status_code = 429
    return _error_response(
        str(error),
        status_code,
        request_id=error.request_id,
    )


def _audio_response(generated_audio: GeneratedAudio) -> Response:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response = Response(generated_audio.audio, mimetype="audio/wav")
    response.headers["Content-Disposition"] = (
        f'inline; filename="concierge_byteplus_{timestamp}_16k.wav"'
    )
    response.headers["X-Audio-Sample-Rate"] = str(generated_audio.wav_info.sample_rate)
    response.headers["X-Audio-Channels"] = str(generated_audio.wav_info.channels)
    response.headers["X-Audio-Duration-Ms"] = str(
        round(generated_audio.wav_info.duration_seconds * 1000)
    )
    response.headers["X-Audio-Sample-Width"] = str(
        generated_audio.wav_info.sample_width_bytes
    )
    if generated_audio.usage_characters is not None:
        response.headers["X-Usage-Characters"] = str(
            generated_audio.usage_characters
        )
    if generated_audio.trace_id:
        response.headers["X-BytePlus-Request-Id"] = generated_audio.trace_id
    return response


def _error_response(
    message: str,
    status_code: int,
    *,
    request_id: str | None = None,
) -> tuple[Response, int]:
    payload: dict[str, str] = {"error": message}
    if request_id:
        payload["request_id"] = request_id
    return jsonify(payload), status_code
