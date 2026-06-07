from __future__ import annotations

from typing import Protocol

from flask import Flask, redirect, render_template, request, url_for

from see_the_growth.domain import TodoDomainError, TodoFilter, TodoItem
from see_the_growth.domain.tag import TagSummary, parse_tag_names
from see_the_growth.domain.todo_filter import parse_todo_filter_from_query
from see_the_growth.services.factory import create_default_todo_service


class TodoFacade(Protocol):
    def create_todo(
        self, title: str, tag_names: list[str] | None = None
    ) -> TodoItem:
        ...

    def list_todos(self, todo_filter: TodoFilter | None = None) -> list[TodoItem]:
        ...

    def tags_for_todo(self, todo_id: str) -> list[str]:
        ...

    def complete_todo(self, todo_id: str) -> None:
        ...

    def flush_completed(self) -> None:
        ...

    def list_tag_summaries(self) -> list[TagSummary]:
        ...

    def delete_tag(self, tag_name: str) -> None:
        ...


def _todo_filter_from_request() -> TodoFilter:
    return parse_todo_filter_from_query(
        tag_param=request.args.get("tag", ""),
        tag_match_param=request.args.get("tag_match", ""),
    )


def _todo_page_url(todo_filter: TodoFilter | None = None) -> str:
    if todo_filter is None or not todo_filter.is_active:
        return url_for("todo_page")
    return f"{url_for('todo_page')}?{todo_filter.to_query_string()}"


def _todo_rows(
    todo_items: list[TodoItem], facade: TodoFacade
) -> list[tuple[TodoItem, list[str]]]:
    return [(todo, facade.tags_for_todo(todo.id)) for todo in todo_items]


def _render_tags_page(
    todos_backend: TodoFacade,
    *,
    error_message: str | None = None,
    status_code: int = 200,
):
    return (
        render_template(
            "tags_page.html",
            tag_summaries=todos_backend.list_tag_summaries(),
            active_nav="tags",
            error_message=error_message,
        ),
        status_code,
    )


def _delete_tag_error_status(exc: TodoDomainError) -> int:
    if "cannot be deleted" in str(exc).lower():
        return 400
    return 404


def _render_todo_page(
    todos_backend: TodoFacade,
    *,
    todos: list[TodoItem],
    error_message: str | None,
    active_filter: TodoFilter,
    status_code: int = 200,
):
    return (
        render_template(
            "todo_page.html",
            todos=todos,
            todo_rows=_todo_rows(todos, todos_backend),
            error_message=error_message,
            active_nav="todo",
            active_filter=active_filter,
            active_filter_query=active_filter.to_query_string(),
        ),
        status_code,
    )


def create_app(todo_list: TodoFacade | None = None) -> Flask:
    app = Flask(__name__)
    app.config["TODO_LIST"] = todo_list or create_default_todo_service()

    @app.get("/")
    def todo_page():
        todos_backend = app.config["TODO_LIST"]
        try:
            active_filter = _todo_filter_from_request()
        except TodoDomainError as exc:
            return _render_todo_page(
                todos_backend,
                todos=[],
                error_message=str(exc),
                active_filter=TodoFilter.none(),
                status_code=400,
            )
        todos = todos_backend.list_todos(todo_filter=active_filter)
        return _render_todo_page(
            todos_backend,
            todos=todos,
            error_message=None,
            active_filter=active_filter,
        )

    @app.get("/tags")
    def tags_page():
        return _render_tags_page(app.config["TODO_LIST"])

    @app.post("/tags/<tag_name>/delete")
    def delete_tag(tag_name: str):
        todos = app.config["TODO_LIST"]
        try:
            todos.delete_tag(tag_name)
        except TodoDomainError as exc:
            return _render_tags_page(
                todos,
                error_message=str(exc),
                status_code=_delete_tag_error_status(exc),
            )
        return redirect(url_for("tags_page"))

    @app.post("/todos")
    def create_todo():
        title = request.form.get("title", "")
        raw_tags = request.form.get("tags", "")
        todos = app.config["TODO_LIST"]
        active_filter = TodoFilter.none()
        try:
            active_filter = _todo_filter_from_request()
            tag_names = parse_tag_names(raw_tags) or None
            todos.create_todo(title, tag_names=tag_names)
        except TodoDomainError as exc:
            listed = todos.list_todos(todo_filter=active_filter)
            return _render_todo_page(
                todos_backend=todos,
                todos=listed,
                error_message=str(exc),
                active_filter=active_filter,
                status_code=400,
            )
        return redirect(_todo_page_url(active_filter))

    @app.post("/todos/<todo_id>/complete")
    def complete_todo(todo_id: str):
        todos = app.config["TODO_LIST"]
        active_filter = TodoFilter.none()
        try:
            active_filter = _todo_filter_from_request()
            todos.complete_todo(todo_id)
        except TodoDomainError as exc:
            listed = todos.list_todos(todo_filter=active_filter)
            return _render_todo_page(
                todos_backend=todos,
                todos=listed,
                error_message=str(exc),
                active_filter=active_filter,
                status_code=404,
            )
        return redirect(_todo_page_url(active_filter))

    @app.post("/todos/flush-completed")
    def flush_completed():
        todos = app.config["TODO_LIST"]
        active_filter = _todo_filter_from_request()
        todos.flush_completed()
        return redirect(_todo_page_url(active_filter))

    return app
