"""MiniMax Studio page route."""

from __future__ import annotations

from flask import Blueprint, render_template


def register_minimax_ui(blueprint: Blueprint) -> None:
    @blueprint.get("/")
    def minimax_index() -> str:
        return render_template("minimax.html", active_provider="minimax")
