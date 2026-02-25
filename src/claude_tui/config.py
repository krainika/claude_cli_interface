"""Configuration dataclass loaded from environment variables / .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load from ~/.claude_tui/.env first, then local .env (local takes precedence)
_config_dir = Path.home() / ".claude_tui"
_config_dir.mkdir(parents=True, exist_ok=True)
load_dotenv(_config_dir / ".env")
load_dotenv(override=True)  # local .env overrides persisted key


def save_api_key(key: str) -> None:
    """Persist the API key to ~/.claude_tui/.env."""
    env_path = _config_dir / ".env"
    env_path.write_text(f"ANTHROPIC_API_KEY={key}\n", encoding="utf-8")
    env_path.chmod(0o600)  # readable only by the owner


@dataclass
class Config:
    api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    default_model: str = field(
        default_factory=lambda: os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
    )
    sessions_dir: Path = field(
        default_factory=lambda: Path.home() / ".claude_tui" / "sessions"
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.environ.get("CLAUDE_MAX_TOKENS", "8096"))
    )
    system_prompt: str = field(
        default_factory=lambda: os.environ.get(
            "CLAUDE_SYSTEM_PROMPT",
            "You are Claude, an AI assistant made by Anthropic. Be helpful, harmless, and honest.",
        )
    )

    def __post_init__(self) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)


# Singleton config instance
config = Config()
