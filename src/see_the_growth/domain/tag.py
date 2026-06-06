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
