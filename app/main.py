"""Flask application entrypoint for all TTS UIs and APIs."""

from __future__ import annotations

import logging
from pathlib import Path
from component.common.tts_history import TtsHistory

from flask import Flask

from app.api_tts.service import create_api_tts_blueprint
from app.context import ApplicationContext, create_context
from app.ui_tts import create_ui_tts_blueprint
from component.byteplus.tts_service import ByteplusTtsService
from component.minimax.tts_service import MinimaxTtsService
from config.settings import Settings


def create_app(
    *,
    settings: Settings | None = None,
    minimax_tts_service: MinimaxTtsService | None = None,
    byteplus_tts_service: ByteplusTtsService | None = None,
    tts_service: MinimaxTtsService | None = None,
    history_root: Path | None = None,
) -> Flask:
    """Create the Flask app with explicit, testable dependencies."""

    runtime_settings = settings or Settings.from_env()
    created_context = create_context(runtime_settings)
    context = ApplicationContext(
        settings=runtime_settings,
        minimax_tts_service=(
            minimax_tts_service or tts_service or created_context.minimax_tts_service
        ),
        byteplus_tts_service=(
            byteplus_tts_service or created_context.byteplus_tts_service
        ),
    )

    app = Flask(__name__)
    app.extensions["tts_history"] = TtsHistory(history_root or Path(__file__).resolve().parents[1] / "output" / "tts")
    app.config.update(
        JSON_AS_ASCII=False,
        MAX_CONTENT_LENGTH=runtime_settings.system.max_content_length,
    )
    app.extensions["application_context"] = context
    app.extensions["minimax_tts_service"] = context.minimax_tts_service
    app.extensions["byteplus_tts_service"] = context.byteplus_tts_service
    app.register_blueprint(create_ui_tts_blueprint())
    app.register_blueprint(
        create_api_tts_blueprint(
            minimax_tts_service=context.minimax_tts_service,
            byteplus_tts_service=context.byteplus_tts_service,
        )
    )
    return app


def demo_app() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings.from_env()
    app = create_app(settings=settings)
    app.run(
        host=settings.system.flask_host,
        port=settings.system.flask_port,
        debug=settings.system.flask_debug,
    )


def main() -> None:
    demo_app()


if __name__ == "__main__":
    main()
