from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GenerationResult = dict[str, Any]
ConversionPlan = dict[str, Any]
RouteInfo = dict[str, Any]
MigrationReport = dict[str, Any]

_SUPPORTED_FASTAPI_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}
_DEFAULT_REQUIREMENTS = [
    "fastapi",
    "uvicorn[standard]",
]


def build_migration_report(
    analyzed_routes: list[RouteInfo],
    converted_routes: list[RouteInfo],
) -> MigrationReport:
    """Summarize conversion coverage and unsupported patterns."""

    unsupported_patterns: list[str] = []
    unconverted_handlers: list[str] = []

    for route in converted_routes:
        unsupported_patterns.extend(route.get("unsupported", []))
        if not route.get("converted", False):
            handler_name = route.get("handler")
            if handler_name:
                unconverted_handlers.append(str(handler_name))

    return {
        "routes_detected": len(analyzed_routes),
        "routes_converted": sum(1 for route in converted_routes if route.get("converted", False)),
        "unsupported_patterns": _unique_strings([str(item) for item in unsupported_patterns]),
        "unconverted_handlers": _unique_strings(unconverted_handlers),
    }


def write_migration_report(
    out_dir: str | Path,
    analyzed_routes: list[RouteInfo],
    converted_routes: list[RouteInfo],
    *,
    filename: str = "MIGRATION_REPORT.json",
) -> Path:
    """Write a migration report JSON file to the output directory."""

    output_root = Path(out_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / filename
    report_path.write_text(
        json.dumps(build_migration_report(analyzed_routes, converted_routes), indent=2),
        encoding="utf-8",
    )
    return report_path


def generate_fastapi_project(
    out_dir: str | Path,
    conversion_plan: ConversionPlan | list[RouteInfo],
) -> GenerationResult:
    """Write a runnable FastAPI project scaffold."""

    output_root = Path(out_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    normalized_plan = _normalize_conversion_plan(conversion_plan)
    main_content = _resolve_main_content(normalized_plan)
    requirements_content = _build_requirements_file(normalized_plan)

    written_files: list[str] = []
    written_files.append(_write_output_file(output_root, "main.py", main_content))
    written_files.append(_write_output_file(output_root, "requirements.txt", requirements_content))

    routes = normalized_plan.get("routes", [])
    report_payload = {
        "summary": "FastAPI scaffold generated.",
        "route_count": len(routes),
        "notes": normalized_plan.get("notes", []),
        "entrypoint": "uvicorn main:app --reload",
        "generated_files": ["main.py", "requirements.txt"],
    }
    report_path = output_root / "migration_report.json"
    report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    written_files.append(report_path.relative_to(output_root).as_posix())

    return {
        "output_dir": str(output_root),
        "written_files": written_files,
        "report": report_payload,
    }


def _normalize_conversion_plan(
    conversion_plan: ConversionPlan | list[RouteInfo],
) -> ConversionPlan:
    if isinstance(conversion_plan, list):
        return {
            "routes": conversion_plan,
            "route_count": len(conversion_plan),
            "notes": [],
            "generated_files": {},
        }
    return conversion_plan


def _resolve_main_content(conversion_plan: ConversionPlan) -> str:
    generated_files = conversion_plan.get("generated_files", {})
    if "main.py" in generated_files:
        return generated_files["main.py"]
    if "app.py" in generated_files:
        return generated_files["app.py"]
    return _build_main_module(conversion_plan.get("routes", []))


def _build_main_module(routes: list[RouteInfo]) -> str:
    lines = [
        "from fastapi import FastAPI",
        "",
        'app = FastAPI(title="Migrated Flask App")',
    ]

    if not routes:
        lines.extend(
            [
                "",
                '@app.get("/")',
                "def root():",
                '    return {"status": "ok"}',
            ]
        )
        return "\n".join(lines) + "\n"

    for route in routes:
        converted_code = route.get("converted_code")
        if converted_code and route.get("converted", True):
            lines.extend(["", str(converted_code)])
            continue

        path = route.get("fastapi_path") or route.get("path") or route.get("source_path") or "/"
        methods = route.get("methods") or ["GET"]
        handler = route.get("handler") or "generated_handler"
        decorator = _build_route_decorator(path, methods)
        signature = route.get("signature") or ""
        body_lines = route.get("body_lines") or [
            f'    return {{"message": "TODO: migrate {handler}"}}'
        ]
        function_prefix = "async def" if route.get("is_async") else "def"

        lines.extend(
            [
                "",
                decorator,
                f"{function_prefix} {handler}({signature}):",
            ]
        )
        lines.extend(body_lines)

    return "\n".join(lines) + "\n"


def _build_route_decorator(path: str, methods: list[str]) -> str:
    if len(methods) == 1 and methods[0].lower() in _SUPPORTED_FASTAPI_METHODS:
        return f'@app.{methods[0].lower()}("{path}")'
    return f'@app.api_route("{path}", methods={methods})'


def _build_requirements_file(conversion_plan: ConversionPlan) -> str:
    existing_requirements = conversion_plan.get("requirements")
    if existing_requirements:
        requirements = [str(item).strip() for item in existing_requirements if str(item).strip()]
    else:
        requirements = list(_DEFAULT_REQUIREMENTS)
    return "\n".join(requirements) + "\n"


def _write_output_file(output_root: Path, relative_path: str, content: str) -> str:
    file_path = output_root / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path.relative_to(output_root).as_posix()


def _unique_strings(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values
