"""Composition root dependencies shared by UI and API."""

from __future__ import annotations

from dataclasses import dataclass

from component.byteplus.tts_service import ByteplusTtsService
from component.minimax.tts_service import MinimaxTtsService
from config.settings import Settings
from util.byteplus_tts_helper import ByteplusTtsHelper
from util.minimax_tts_helper import MinimaxTtsHelper
from util.wav_helper import WavHelper


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    settings: Settings
    minimax_tts_service: MinimaxTtsService
    byteplus_tts_service: ByteplusTtsService


def create_context(settings: Settings) -> ApplicationContext:
    system = settings.system
    wav_helper = WavHelper(
        required_sample_rate=system.audio_sample_rate,
        required_channels=system.audio_channels,
    )
    minimax_helper = MinimaxTtsHelper(
        api_key=settings.minimax.api_key,
        base_url=settings.minimax.api_base_url,
        connect_timeout_seconds=settings.minimax.connect_timeout_seconds,
        read_timeout_seconds=settings.minimax.read_timeout_seconds,
    )
    byteplus_helper = ByteplusTtsHelper(
        api_key=settings.byteplus.api_key,
        base_url=settings.byteplus.api_base_url,
        resource_id=settings.byteplus.resource_id,
        user_id=settings.byteplus.user_id,
        connect_timeout_seconds=settings.byteplus.connect_timeout_seconds,
        read_timeout_seconds=settings.byteplus.read_timeout_seconds,
    )
    return ApplicationContext(
        settings=settings,
        minimax_tts_service=MinimaxTtsService(
            minimax_helper=minimax_helper,
            wav_helper=wav_helper,
            voice_cache_seconds=settings.minimax.voice_cache_seconds,
            max_segments=settings.minimax.max_segments,
        ),
        byteplus_tts_service=ByteplusTtsService(
            byteplus_helper=byteplus_helper,
            wav_helper=wav_helper,
            max_segments=settings.byteplus.max_segments,
        ),
    )


def demo_context() -> None:
    context = create_context(Settings.from_env())
    print(
        {
            "minimax_configured": context.minimax_tts_service.is_configured,
            "byteplus_configured": context.byteplus_tts_service.is_configured,
            "sample_rate": context.settings.system.audio_sample_rate,
        }
    )


def main() -> None:
    demo_context()


if __name__ == "__main__":
    main()
