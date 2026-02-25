"""File and image attachment loaders → ContentBlock types."""

from __future__ import annotations

import base64
from pathlib import Path

from claude_tui.session import DocumentContent, ImageContent, TextContent

# Size limits
IMAGE_MAX_BYTES = 5 * 1024 * 1024    # 5 MB
PDF_MAX_BYTES = 5 * 1024 * 1024      # 5 MB
TEXT_MAX_BYTES = 200 * 1024          # 200 KB

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
PDF_EXTENSIONS = {".pdf"}

IMAGE_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


class AttachmentError(Exception):
    """Raised when a file cannot be attached."""


def load_attachment(path: str | Path) -> ImageContent | DocumentContent | TextContent:
    """
    Load a file from disk and return an appropriate ContentBlock.

    Raises AttachmentError on size violations or unknown types.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise AttachmentError(f"File not found: {p}")
    if not p.is_file():
        raise AttachmentError(f"Not a file: {p}")

    ext = p.suffix.lower()
    size = p.stat().st_size

    if ext in IMAGE_EXTENSIONS:
        if size > IMAGE_MAX_BYTES:
            raise AttachmentError(
                f"Image too large: {size / 1024 / 1024:.1f} MB (max 5 MB)"
            )
        data = base64.standard_b64encode(p.read_bytes()).decode()
        media_type = IMAGE_MEDIA_TYPES[ext]
        return ImageContent(data=data, media_type=media_type)

    if ext in PDF_EXTENSIONS:
        if size > PDF_MAX_BYTES:
            raise AttachmentError(
                f"PDF too large: {size / 1024 / 1024:.1f} MB (max 5 MB)"
            )
        data = base64.standard_b64encode(p.read_bytes()).decode()
        return DocumentContent(data=data, media_type="application/pdf", filename=p.name)

    # Treat everything else as a text/code file
    if size > TEXT_MAX_BYTES:
        raise AttachmentError(
            f"Text file too large: {size / 1024:.0f} KB (max 200 KB)"
        )
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise AttachmentError(
            f"Cannot read file as UTF-8 text: {p.name}"
        ) from e

    # Wrap in a fenced code block so Claude sees syntax context
    lang = ext.lstrip(".") if ext else "text"
    wrapped = f"**{p.name}**\n\n```{lang}\n{text}\n```"
    return DocumentContent(data=wrapped, media_type="text/plain", filename=p.name)
