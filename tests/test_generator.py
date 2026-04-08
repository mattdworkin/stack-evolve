import ast

from report.migration_report import generate_fastapi_project


def test_generate_fastapi_project_writes_main_requirements_and_report(tmp_path):
    converted_routes = [
        {
            "path": "/users",
            "fastapi_path": "/users",
            "methods": ["GET"],
            "handler": "get_users",
            "converted": True,
            "file": "app.py",
        }
    ]

    result = generate_fastapi_project(tmp_path, converted_routes)

    main_text = (tmp_path / "main.py").read_text(encoding="utf-8")
    requirements_text = (tmp_path / "requirements.txt").read_text(encoding="utf-8")

    assert result["written_files"] == ["main.py", "requirements.txt"]
    assert "from fastapi import FastAPI, HTTPException" in main_text
    assert "from fastapi.responses import JSONResponse" in main_text
    assert "app = FastAPI()" in main_text
    assert '@app.get("/users")' in main_text
    assert "def get_users():" in main_text
    assert 'return {"message": "TODO: migrate get_users"}' in main_text
    assert "fastapi" in requirements_text
    assert "uvicorn[standard]" in requirements_text
    assert result["entrypoint"] == "uvicorn main:app --reload"
    ast.parse(main_text)


def test_generate_fastapi_project_skips_unconverted_routes(tmp_path):
    conversion_plan = {
        "routes": [
            {
                "fastapi_path": "/health",
                "methods": ["GET"],
                "handler": "health",
                "converted_code": '@app.get("/health")\ndef health():\n    return {"ok": True}',
                "converted": True,
            },
            {
                "fastapi_path": "/submit",
                "methods": ["POST"],
                "handler": "submit_form",
                "converted_code": '@app.post("/submit")\ndef submit_form():\n    # TODO(migration): unsupported pattern\n    return {"status": "stub"}',
                "converted": False,
            },
        ],
    }

    generate_fastapi_project(tmp_path, conversion_plan)

    main_text = (tmp_path / "main.py").read_text(encoding="utf-8")
    assert "def health():" in main_text
    assert 'return {"ok": True}' in main_text
    assert "def submit_form():" not in main_text
