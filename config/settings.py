"""Environment-backed composition of system and provider configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from config.byteplus_config import ByteplusConfig
from config.minimax_config import MinimaxConfig
from config.system_config import SystemConfig


@dataclass(frozen=True, slots=True)
class Settings:
    system: SystemConfig
    minimax: MinimaxConfig
    byteplus: ByteplusConfig

    @classmethod
    def from_env(cls) -> "Settings":
        project_root = Path(__file__).resolve().parents[1]
        load_dotenv(project_root / ".env", override=False)
        load_dotenv(project_root / "app" / ".env", override=False)
        return cls(
            system=SystemConfig.from_env(),
            minimax=MinimaxConfig.from_env(),
            byteplus=ByteplusConfig.from_env(),
        )


def demo_settings() -> None:
    settings = Settings.from_env()
    print(
        {
            "minimax_configured": bool(settings.minimax.api_key),
            "byteplus_configured": bool(settings.byteplus.api_key),
            "flask_address": (
                f"{settings.system.flask_host}:{settings.system.flask_port}"
            ),
            "sample_rate": settings.system.audio_sample_rate,
        }
    )


def main() -> None:
    demo_settings()


if __name__ == "__main__":
    main()
