from pathlib import Path

from analyzer.route_analyzer import analyze_flask_routes
from converter.flask_to_fastapi import convert_flask_to_fastapi


def test_convert_flask_to_fastapi_preserves_basic_sample_behavior():
    repo_root = Path(__file__).resolve().parents[1]
    sample_app_path = repo_root / "sample_apps" / "flask_simple"

    routes = analyze_flask_routes(sample_app_path)
    conversion_plan = convert_flask_to_fastapi(sample_app_path, routes)
    generated_app = conversion_plan["generated_files"]["app.py"]

    assert conversion_plan["routes"] == [
        {
            "source_path": "/health",
            "fastapi_path": "/health",
            "methods": ["GET"],
            "handler": "health",
            "file": "app.py",
            "issues": [],
        },
        {
            "source_path": "/users/<int:user_id>",
            "fastapi_path": "/users/{user_id}",
            "methods": ["GET"],
            "handler": "get_user",
            "file": "app.py",
            "issues": [],
        },
    ]
    assert "def health():" in generated_app
    assert "return {'ok': True}" in generated_app
    assert "@app.get(\"/users/{user_id}\")" in generated_app
    assert "def get_user(user_id: int, q: Optional[str] = None):" in generated_app
    assert "raise HTTPException(status_code=404)" in generated_app
    assert "status_code=200" in generated_app


def test_convert_flask_to_fastapi_with_mock_routes_input():
    repo_root = Path(__file__).resolve().parents[1]
    sample_app_path = repo_root / "sample_apps" / "flask_simple"

    mock_routes = [
        {
            "path": "/users/<int:id>",
            "methods": ["GET"],
            "handler": "get_user",
            "file": "app.py",
        },
        {
            "path": "/users",
            "methods": ["POST"],
            "handler": "create_user",
            "file": "app.py",
        },
    ]

    conversion_plan = convert_flask_to_fastapi(sample_app_path, mock_routes)
    generated_app = conversion_plan["generated_files"]["app.py"]

    assert conversion_plan["routes"] == [
        {
            "source_path": "/users/<int:id>",
            "fastapi_path": "/users/{id}",
            "methods": ["GET"],
            "handler": "get_user",
            "file": "app.py",
            "issues": [],
        },
        {
            "source_path": "/users",
            "fastapi_path": "/users",
            "methods": ["POST"],
            "handler": "create_user",
            "file": "app.py",
            "issues": ["Handler body was not found; inserted a stub body."],
        },
    ]
    assert '@app.get("/users/{id}")' in generated_app
    assert "@app.post(\"/users\")" in generated_app
