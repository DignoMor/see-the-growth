"""Tag name normalization and summary types (SPEC-008)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TagSummary:
    name: str
    unfinished_count: int


def normalize_tag_name(name: str) -> str:
    from .todo_list import TodoDomainError

    normalized = re.sub(r"\s+", " ", name.strip()).lower()
    if not normalized:
        raise TodoDomainError("Tag name must not be empty.")
    return normalized


def parse_tag_names(raw: str) -> list[str]:
    """Parse comma-separated tag input (SPEC-009)."""
    if not raw.strip():
        return []

    seen: set[str] = set()
    parsed: list[str] = []
    for segment in raw.split(","):
        trimmed = segment.strip()
        if not trimmed:
            continue
        normalized = normalize_tag_name(trimmed)
        if normalized not in seen:
            seen.add(normalized)
            parsed.append(normalized)
    return parsed
