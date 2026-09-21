"""BytePlus Studio page route."""

from __future__ import annotations

from flask import Blueprint, render_template


def register_byteplus_ui(blueprint: Blueprint) -> None:
    @blueprint.get("/byteplus")
    def byteplus_index() -> str:
        return render_template("byteplus.html", active_provider="byteplus")
