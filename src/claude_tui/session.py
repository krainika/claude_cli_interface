"""ChatMessage, Session data models and JSON persistence."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Content block types
# ---------------------------------------------------------------------------

@dataclass
class TextContent:
    text: str
    type: Literal["text"] = "text"

    def to_api_format(self) -> dict[str, Any]:
        return {"type": "text", "text": self.text}

    def to_dict(self) -> dict[str, Any]:
        return {"type": "text", "text": self.text}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TextContent":
        return cls(text=d["text"])


@dataclass
class ImageContent:
    data: str          # base64-encoded
    media_type: str    # e.g. "image/png"
    type: Literal["image"] = "image"

    def to_api_format(self) -> dict[str, Any]:
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": self.media_type,
                "data": self.data,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {"type": "image", "media_type": self.media_type, "data": self.data}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ImageContent":
        return cls(data=d["data"], media_type=d["media_type"])


@dataclass
class DocumentContent:
    data: str          # base64-encoded (PDF) or plain text
    media_type: str    # "application/pdf" or "text/plain"
    filename: str = ""
    type: Literal["document"] = "document"

    def to_api_format(self) -> dict[str, Any]:
        if self.media_type == "text/plain":
            return {
                "type": "document",
                "source": {
                    "type": "text",
                    "media_type": self.media_type,
                    "data": self.data,
                },
            }
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": self.media_type,
                "data": self.data,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "document",
            "media_type": self.media_type,
            "filename": self.filename,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DocumentContent":
        return cls(
            data=d["data"],
            media_type=d["media_type"],
            filename=d.get("filename", ""),
        )


ContentBlock = TextContent | ImageContent | DocumentContent


def content_block_from_dict(d: dict[str, Any]) -> ContentBlock:
    match d["type"]:
        case "text":
            return TextContent.from_dict(d)
        case "image":
            return ImageContent.from_dict(d)
        case "document":
            return DocumentContent.from_dict(d)
        case _:
            raise ValueError(f"Unknown content block type: {d['type']}")


# ---------------------------------------------------------------------------
# ChatMessage
# ---------------------------------------------------------------------------

@dataclass
class ChatMessage:
    role: Literal["user", "assistant"]
    content: list[ContentBlock]
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_api_format(self) -> dict[str, Any]:
        """Convert to the exact Anthropic API messages array format."""
        blocks = [block.to_api_format() for block in self.content]
        # Flatten to string if single text block (API accepts both)
        if len(blocks) == 1 and blocks[0]["type"] == "text":
            return {"role": self.role, "content": blocks[0]["text"]}
        return {"role": self.role, "content": blocks}

    def text_preview(self) -> str:
        """Return a short text preview for display."""
        for block in self.content:
            if isinstance(block, TextContent):
                return block.text[:80]
        return "[attachment]"

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "role": self.role,
            "content": [block.to_dict() for block in self.content],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ChatMessage":
        return cls(
            role=d["role"],
            content=[content_block_from_dict(b) for b in d["content"]],
            message_id=d.get("message_id", str(uuid.uuid4())),
            created_at=d.get("created_at", datetime.now(timezone.utc).isoformat()),
        )


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

@dataclass
class Session:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    messages: list[ChatMessage] = field(default_factory=list)

    def add_message(self, msg: ChatMessage) -> None:
        self.messages.append(msg)
        self.updated_at = datetime.now(timezone.utc).isoformat()
        # Auto-title from first user message
        if self.title == "New Conversation" and msg.role == "user":
            preview = msg.text_preview()
            self.title = preview[:50] + ("…" if len(preview) > 50 else "")

    def to_api_messages(self) -> list[dict[str, Any]]:
        return [msg.to_api_format() for msg in self.messages]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [msg.to_dict() for msg in self.messages],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Session":
        return cls(
            session_id=d["session_id"],
            title=d.get("title", "Conversation"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            messages=[ChatMessage.from_dict(m) for m in d.get("messages", [])],
        )

    def save(self, sessions_dir: Path) -> None:
        path = sessions_dir / f"{self.session_id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Session":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)


def list_sessions(sessions_dir: Path) -> list[Session]:
    """Return all sessions sorted by updated_at descending."""
    sessions = []
    for p in sessions_dir.glob("*.json"):
        try:
            sessions.append(Session.load(p))
        except Exception:
            pass
    sessions.sort(key=lambda s: s.updated_at, reverse=True)
    return sessions
