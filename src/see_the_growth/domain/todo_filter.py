"""Todo list filter criteria (SPEC-009)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlencode

from .tag import parse_tag_names


class TagMatchMode(Enum):
    """How multiple tag names in a filter combine."""

    ANY = "any"
    ALL = "all"


@dataclass(frozen=True)
class TodoFilter:
    """Criteria for restricting which visible todos are listed."""

    tag_names: tuple[str, ...] = ()
    tag_match: TagMatchMode = TagMatchMode.ANY

    @property
    def is_active(self) -> bool:
        return bool(self.tag_names)

    @property
    def display_label(self) -> str:
        if not self.tag_names:
            return ""
        quoted = ", ".join(f'"{name}"' for name in self.tag_names)
        if self.tag_match == TagMatchMode.ALL:
            return f"{quoted} (all)"
        return quoted

    @classmethod
    def none(cls) -> TodoFilter:
        return cls()

    @classmethod
    def for_single_tag(cls, tag_name: str) -> TodoFilter:
        return cls.for_tags([tag_name])

    @classmethod
    def for_tags(
        cls,
        tag_names: list[str],
        *,
        match: TagMatchMode = TagMatchMode.ANY,
    ) -> TodoFilter:
        seen: set[str] = set()
        deduped: list[str] = []
        for name in tag_names:
            if name not in seen:
                seen.add(name)
                deduped.append(name)
        return cls(tag_names=tuple(deduped), tag_match=match)

    def matches(self, todo_tag_names: set[str]) -> bool:
        if not self.is_active:
            return True
        required = set(self.tag_names)
        if self.tag_match == TagMatchMode.ALL:
            return required.issubset(todo_tag_names)
        return bool(required & todo_tag_names)

    def to_query_string(self) -> str:
        if not self.is_active:
            return ""
        params: dict[str, str] = {"tag": ",".join(self.tag_names)}
        if self.tag_match != TagMatchMode.ANY:
            params["tag_match"] = self.tag_match.value
        return urlencode(params)


def parse_tag_match_mode(raw: str) -> TagMatchMode:
    from .todo_list import TodoDomainError

    value = raw.strip().lower()
    if value in ("", "any"):
        return TagMatchMode.ANY
    if value == "all":
        return TagMatchMode.ALL
    raise TodoDomainError(f"Unknown tag match mode '{raw}'.")


def parse_todo_filter_from_query(
    tag_params: str | list[str] = "",
    tag_match_param: str = "",
) -> TodoFilter:
    """Build a filter from query params (SPEC-009, SPEC-011).

    Accepts a single comma-separated string or a list of tag param values
    (for example repeated ``tag`` keys from a checkbox GET form).
    """
    tag_match = parse_tag_match_mode(tag_match_param)
    raw_values: list[str]
    if isinstance(tag_params, str):
        raw_values = [tag_params] if tag_params else []
    else:
        raw_values = list(tag_params)

    tag_names: list[str] = []
    seen: set[str] = set()
    for raw in raw_values:
        if not raw.strip():
            continue
        for name in parse_tag_names(raw):
            if name not in seen:
                seen.add(name)
                tag_names.append(name)

    if not tag_names:
        return TodoFilter.none()
    return TodoFilter.for_tags(tag_names, match=tag_match)
