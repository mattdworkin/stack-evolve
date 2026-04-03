import json
from pathlib import Path

from report.migration_report import build_migration_report, write_migration_report


def test_build_migration_report_summarizes_conversion_status():
    analyzed_routes = [
        {"path": "/users", "handler": "get_users"},
        {"path": "/submit", "handler": "submit_form"},
    ]
    converted_routes = [
        {
            "handler": "get_users",
            "converted": True,
            "unsupported": [],
        },
        {
            "handler": "submit_form",
            "converted": False,
            "unsupported": ["request.form", "session usage"],
        },
    ]

    assert build_migration_report(analyzed_routes, converted_routes) == {
        "routes_detected": 2,
        "routes_converted": 1,
        "unsupported_patterns": ["request.form", "session usage"],
        "unconverted_handlers": ["submit_form"],
    }


def test_write_migration_report_creates_json_file(monkeypatch):
    writes: dict[str, str] = {}

    def fake_mkdir(self, parents=False, exist_ok=False):
        return None

    def fake_write_text(self, content, encoding=None):
        writes[str(self)] = content
        return len(content)

    monkeypatch.setattr(Path, "mkdir", fake_mkdir)
    monkeypatch.setattr(Path, "write_text", fake_write_text)

    report_path = write_migration_report(
        "out_fastapi",
        analyzed_routes=[{"handler": "health"}],
        converted_routes=[{"handler": "health", "converted": True, "unsupported": []}],
    )

    assert report_path.name == "MIGRATION_REPORT.json"
    assert json.loads(writes[str(report_path)]) == {
        "routes_detected": 1,
        "routes_converted": 1,
        "unsupported_patterns": [],
        "unconverted_handlers": [],
    }
