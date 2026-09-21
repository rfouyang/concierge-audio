"""Shared TTS UI blueprint and provider page registration."""

from __future__ import annotations

from flask import Blueprint

from app.ui_tts.byteplus.ui_byteplus import register_byteplus_ui
from app.ui_tts.minimax.ui_minimax import register_minimax_ui


def create_ui_tts_blueprint() -> Blueprint:
    blueprint = Blueprint(
        "tts_ui",
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/tts-static",
    )
    register_minimax_ui(blueprint)
    register_byteplus_ui(blueprint)
    return blueprint
