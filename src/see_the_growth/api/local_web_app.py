from __future__ import annotations

from typing import Protocol

from flask import Flask, redirect, render_template, request, session, url_for

from see_the_growth.api.auth import (
    clear_authentication,
    is_authenticated,
    mark_authenticated,
    safe_redirect_target,
    secret_key_for_gate_password,
    verify_gate_password,
)
from see_the_growth.api.auth_config import AuthConfig, resolve_auth_config
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
        tag_params=request.args.getlist("tag"),
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
            tag_summaries=todos_backend.list_tag_summaries(),
            error_message=error_message,
            active_nav="todo",
            active_filter=active_filter,
            active_filter_query=active_filter.to_query_string(),
        ),
        status_code,
    )


def _auth_config_from_app(app: Flask) -> AuthConfig:
    return app.config["AUTH_CONFIG"]


def _render_login_page(
    *,
    error_message: str | None = None,
    next_url: str | None = None,
    status_code: int = 200,
):
    return (
        render_template(
            "login_page.html",
            error_message=error_message,
            next_url=next_url,
            auth_enabled=True,
            show_logout=False,
        ),
        status_code,
    )


def create_app(
    todo_list: TodoFacade | None = None,
    auth_config: AuthConfig | None = None,
) -> Flask:
    app = Flask(__name__)
    app.config["TODO_LIST"] = todo_list or create_default_todo_service()
    resolved_auth = auth_config if auth_config is not None else resolve_auth_config()
    app.config["AUTH_CONFIG"] = resolved_auth
    if resolved_auth.enabled and resolved_auth.gate_password is not None:
        app.secret_key = secret_key_for_gate_password(resolved_auth.gate_password)

    @app.before_request
    def require_gate_password():
        auth = _auth_config_from_app(app)
        if not auth.enabled:
            return None
        if request.path == "/health":
            return None
        if request.path.startswith("/static/"):
            return None
        if request.path == "/login":
            return None
        if is_authenticated(session):
            return None
        return redirect(url_for("login", next=request.full_path.rstrip("?")))

    @app.context_processor
    def inject_auth_context():
        auth = _auth_config_from_app(app)
        return {
            "auth_enabled": auth.enabled,
            "show_logout": auth.enabled and is_authenticated(session),
        }

    @app.get("/login")
    def login():
        auth = _auth_config_from_app(app)
        if not auth.enabled:
            return redirect(url_for("todo_page"))
        if is_authenticated(session):
            return redirect(safe_redirect_target(request.args.get("next")))
        return _render_login_page(next_url=request.args.get("next"))

    @app.post("/login")
    def login_submit():
        auth = _auth_config_from_app(app)
        if not auth.enabled:
            return redirect(url_for("todo_page"))
        next_url = request.form.get("next")
        submitted = request.form.get("password", "")
        gate_password = auth.gate_password
        if gate_password is None or not verify_gate_password(submitted, gate_password):
            return _render_login_page(
                error_message="Incorrect password",
                next_url=next_url,
                status_code=401,
            )
        mark_authenticated(session)
        return redirect(safe_redirect_target(next_url))

    @app.post("/logout")
    def logout():
        auth = _auth_config_from_app(app)
        if not auth.enabled:
            return redirect(url_for("todo_page"))
        clear_authentication(session)
        return redirect(url_for("login"))

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

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
