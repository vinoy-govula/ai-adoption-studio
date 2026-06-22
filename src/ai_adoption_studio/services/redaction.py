"""Redact sensitive data before Cursor agent calls."""

from __future__ import annotations

import hashlib
import re
from typing import Any

_KEY_PATTERN = re.compile(r"(api[_-]?key|secret|token|password)\s*[:=]\s*\S+", re.I)
_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}")


def redact_text(text: str, *, max_lines: int = 100) -> str:
    lines = text.splitlines()[-max_lines:]
    redacted = []
    for line in lines:
        line = _KEY_PATTERN.sub(r"\1=[REDACTED]", line)
        line = _EMAIL_PATTERN.sub(_hash_email, line)
        redacted.append(line)
    return "\n".join(redacted)


def _hash_email(match: re.Match[str]) -> str:
    digest = hashlib.sha256(match.group(0).encode()).hexdigest()[:8]
    return f"user-{digest}@redacted"


def redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    text = str(data)
    return {"redacted_summary": redact_text(text)}
