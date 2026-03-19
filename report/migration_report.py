from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GenerationResult = dict[str, Any]
ConversionPlan = dict[str, Any]


def generate_fastapi_project(
    out_dir: str | Path,
    conversion_plan: ConversionPlan,
) -> GenerationResult:
    """Write stub FastAPI output files and a migration report."""

    output_root = Path(out_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    generated_files = conversion_plan.get("generated_files", {})
    written_files: list[str] = []

    for relative_path, content in generated_files.items():
        file_path = output_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        written_files.append(file_path.relative_to(output_root).as_posix())

    report_payload = {
        "summary": "Stub migration artifacts generated.",
        "route_count": conversion_plan.get("route_count", 0),
        "notes": conversion_plan.get("notes", []),
    }
    report_path = output_root / "migration_report.json"
    report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    written_files.append(report_path.relative_to(output_root).as_posix())

    return {
        "output_dir": str(output_root),
        "written_files": written_files,
        "report": report_payload,
    }
