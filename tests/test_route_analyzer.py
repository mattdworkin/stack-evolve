from pathlib import Path

from analyzer.route_analyzer import analyze_flask_routes


def test_analyze_flask_routes_extracts_sample_app_routes():
    repo_root = Path(__file__).resolve().parents[1]
    sample_app_path = repo_root / "sample_apps" / "flask_simple"

    assert analyze_flask_routes(sample_app_path) == [
        {
            "path": "/health",
            "methods": ["GET"],
            "handler": "health",
            "file": "app.py",
        },
        {
            "path": "/users/<int:user_id>",
            "methods": ["GET"],
            "handler": "get_user",
            "file": "app.py",
        },
    ]
