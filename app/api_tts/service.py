"""Composition entrypoint for all TTS API blueprints."""

from __future__ import annotations

from flask import Blueprint
from app.api_tts.routes.api_history import create_history_blueprint

from app.api_tts.routes.api_byteplus import create_byteplus_api_blueprint
from app.api_tts.routes.api_minimax import create_minimax_api_blueprint
from component.byteplus.tts_service import ByteplusTtsService
from component.minimax.tts_service import MinimaxTtsService


def create_api_tts_blueprint(
    *,
    minimax_tts_service: MinimaxTtsService,
    byteplus_tts_service: ByteplusTtsService,
) -> Blueprint:
    blueprint = Blueprint("tts_api", __name__, url_prefix="/api")
    blueprint.register_blueprint(create_history_blueprint())
    minimax_blueprint = create_minimax_api_blueprint(minimax_tts_service)
    blueprint.register_blueprint(minimax_blueprint, url_prefix="/minimax")
    blueprint.register_blueprint(
        create_byteplus_api_blueprint(byteplus_tts_service),
        url_prefix="/byteplus",
    )

    # Preserve the existing MiniMax API contract while the namespaced routes
    # become the canonical endpoints used by the new navigation UI.
    blueprint.register_blueprint(
        minimax_blueprint,
        url_prefix="",
        name="minimax_legacy",
    )
    return blueprint
