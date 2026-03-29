import ast
import json

from report.migration_report import generate_fastapi_project


def test_generate_fastapi_project_writes_main_requirements_and_report(tmp_path):
    converted_routes = [
        {
            "path": "/users",
            "methods": ["GET"],
            "handler": "get_users",
            "file": "app.py",
        }
    ]

    result = generate_fastapi_project(tmp_path, converted_routes)

    main_text = (tmp_path / "main.py").read_text(encoding="utf-8")
    requirements_text = (tmp_path / "requirements.txt").read_text(encoding="utf-8")
    report = json.loads((tmp_path / "migration_report.json").read_text(encoding="utf-8"))

    assert result["written_files"] == ["main.py", "requirements.txt", "migration_report.json"]
    assert 'app = FastAPI(title="Migrated Flask App")' in main_text
    assert '@app.get("/users")' in main_text
    assert "def get_users():" in main_text
    assert 'return {"message": "TODO: migrate get_users"}' in main_text
    assert "fastapi" in requirements_text
    assert "uvicorn[standard]" in requirements_text
    assert report["entrypoint"] == "uvicorn main:app --reload"
    ast.parse(main_text)


def test_generate_fastapi_project_uses_converter_generated_app_when_present(tmp_path):
    conversion_plan = {
        "routes": [
            {
                "fastapi_path": "/health",
                "methods": ["GET"],
                "handler": "health",
                "file": "app.py",
            }
        ],
        "notes": ["conversion complete"],
        "generated_files": {
            "app.py": '\n'.join(
                [
                    "from fastapi import FastAPI",
                    "",
                    "app = FastAPI()",
                    "",
                    '@app.get("/health")',
                    "def health():",
                    '    return {"ok": True}',
                    "",
                ]
            )
        },
    }

    generate_fastapi_project(tmp_path, conversion_plan)

    main_text = (tmp_path / "main.py").read_text(encoding="utf-8")
    assert "def health():" in main_text
    assert 'return {"ok": True}' in main_text
