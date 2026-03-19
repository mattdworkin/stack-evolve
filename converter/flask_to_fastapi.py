from __future__ import annotations

from pathlib import Path
from typing import Any

RouteInfo = dict[str, Any]
ConversionPlan = dict[str, Any]


def convert_flask_to_fastapi(
    repo_path: str | Path,
    routes: list[RouteInfo],
) -> ConversionPlan:
    """Build a stub conversion plan from analyzed Flask routes."""

    source_root = Path(repo_path)
    route_summaries = [
        {
            "path": route["path"],
            "methods": route["methods"],
            "handler": route["handler"],
        }
        for route in routes
    ]

    generated_app = _build_fastapi_app(route_summaries)

    return {
        "source_repo": str(source_root),
        "route_count": len(route_summaries),
        "routes": route_summaries,
        "notes": [
            "Stub conversion plan generated from analyzer output.",
            "Handler bodies are placeholders and require manual migration.",
        ],
        "generated_files": {
            "app.py": generated_app,
        },
    }


def _build_fastapi_app(routes: list[RouteInfo]) -> str:
    lines = [
        "from fastapi import FastAPI",
        "",
        'app = FastAPI(title="Migrated Flask App")',
    ]

    if routes:
        for route in routes:
            method = route["methods"][0].lower()
            decorator = f'@app.{method}("{route["path"]}")'
            lines.extend(
                [
                    "",
                    decorator,
                    f'def {route["handler"]}():',
                    '    return {"status": "stub"}',
                ]
            )
    else:
        lines.extend(
            [
                "",
                "@app.get(\"/\")",
                "def root():",
                '    return {"status": "stub"}',
            ]
        )

    return "\n".join(lines) + "\n"
