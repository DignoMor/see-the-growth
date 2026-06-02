from __future__ import annotations

from typing import Protocol

from flask import Flask, redirect, render_template, request, url_for

from see_the_growth.domain import TodoDomainError, TodoItem
from see_the_growth.services.factory import create_default_todo_service


class TodoFacade(Protocol):
    def create_todo(self, title: str) -> TodoItem:
        ...

    def list_todos(self) -> list[TodoItem]:
        ...

    def complete_todo(self, todo_id: str) -> None:
        ...


def create_app(todo_list: TodoFacade | None = None) -> Flask:
    app = Flask(__name__)
    app.config["TODO_LIST"] = todo_list or create_default_todo_service()

    @app.get("/")
    def todo_page():
        todos = app.config["TODO_LIST"].list_todos()
        return render_template("todo_page.html", todos=todos, error_message=None), 200

    @app.post("/todos")
    def create_todo():
        title = request.form.get("title", "")
        todos = app.config["TODO_LIST"]
        try:
            todos.create_todo(title)
        except TodoDomainError as exc:
            return (
                render_template(
                    "todo_page.html",
                    todos=todos.list_todos(),
                    error_message=str(exc),
                ),
                400,
            )
        return redirect(url_for("todo_page"))

    @app.post("/todos/<todo_id>/complete")
    def complete_todo(todo_id: str):
        todos = app.config["TODO_LIST"]
        try:
            todos.complete_todo(todo_id)
        except TodoDomainError as exc:
            return (
                render_template(
                    "todo_page.html",
                    todos=todos.list_todos(),
                    error_message=str(exc),
                ),
                404,
            )
        return redirect(url_for("todo_page"))

    return app
