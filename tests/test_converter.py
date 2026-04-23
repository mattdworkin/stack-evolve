from pathlib import Path
import ast

from analyzer.route_analyzer import analyze_flask_routes
import converter.flask_to_fastapi as flask_to_fastapi
from converter.flask_to_fastapi import convert_flask_to_fastapi


def test_convert_flask_to_fastapi_preserves_basic_sample_behavior():
    repo_root = Path(__file__).resolve().parents[1]
    sample_app_path = repo_root / "sample_apps" / "flask_simple"

    routes = analyze_flask_routes(sample_app_path)
    conversion_plan = convert_flask_to_fastapi(sample_app_path, routes)
    generated_app = conversion_plan["generated_files"]["app.py"]

    assert conversion_plan["routes"] == [
        {
            "original_path": "/health",
            "fastapi_path": "/health",
            "methods": ["GET"],
            "handler": "health",
            "converted_code": '@app.get("/health")\ndef health():\n    return {\'ok\': True}',
            "converted": True,
            "unsupported": [],
        },
        {
            "original_path": "/users/<int:user_id>",
            "fastapi_path": "/users/{user_id}",
            "methods": ["GET"],
            "handler": "get_user",
            "converted_code": '@app.get("/users/{user_id}")\ndef get_user(user_id: int, q: Optional[str] = None):\n    if user_id < 0:\n        raise HTTPException(status_code=404)\n    return JSONResponse(content={\'user_id\': user_id, \'q\': q}, status_code=200)',
            "converted": True,
            "unsupported": [],
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
            "original_path": "/users/<int:id>",
            "fastapi_path": "/users/{id}",
            "methods": ["GET"],
            "handler": "get_user",
            "converted_code": '@app.get("/users/{id}")\ndef get_user(id: int, q: Optional[str] = None):\n    if id < 0:\n        raise HTTPException(status_code=404)\n    return JSONResponse(content={\'user_id\': id, \'q\': q}, status_code=200)',
            "converted": True,
            "unsupported": [],
        },
        {
            "original_path": "/users",
            "fastapi_path": "/users",
            "methods": ["POST"],
            "handler": "create_user",
            "converted_code": '@app.post("/users")\ndef create_user():\n    # TODO(migration): unsupported pattern\n    return {"status": "stub"}',
            "converted": False,
            "unsupported": ["missing handler body"],
        },
    ]
    assert '@app.get("/users/{id}")' in generated_app
    assert "@app.post(\"/users\")" in generated_app


def test_convert_flask_to_fastapi_marks_unsupported_patterns(monkeypatch):
    handler_source = "\n".join(
        [
            "def submit_form():",
            '    name = request.form.get("name")',
            '    return jsonify({"name": name})',
        ]
    )
    handler_node = ast.parse(handler_source).body[0]

    def fake_build_handler_index(search_root, routes):
        return {("app.py", "submit_form"): handler_node}

    monkeypatch.setattr(flask_to_fastapi, "_build_handler_index", fake_build_handler_index)

    conversion_plan = convert_flask_to_fastapi(
        "sample_apps/flask_simple",
        [
            {
                "path": "/submit",
                "methods": ["POST"],
                "handler": "submit_form",
                "file": "app.py",
            }
        ],
    )

    assert conversion_plan["routes"] == [
        {
            "original_path": "/submit",
            "fastapi_path": "/submit",
            "methods": ["POST"],
            "handler": "submit_form",
            "converted_code": '@app.post("/submit")\ndef submit_form():\n    # TODO(migration): unsupported pattern\n    name = request.form.get(\'name\')\n    return {\'name\': name}',
            "converted": False,
            "unsupported": ["request.form"],
        }
    ]


def test_convert_flask_to_fastapi_marks_render_template_as_unsupported(monkeypatch):
    handler_source = "\n".join(
        [
            "def hello_world():",
            '    return render_template("index.html")',
        ]
    )
    handler_node = ast.parse(handler_source).body[0]

    def fake_build_handler_index(search_root, routes):
        return {("app.py", "hello_world"): handler_node}

    monkeypatch.setattr(flask_to_fastapi, "_build_handler_index", fake_build_handler_index)

    conversion_plan = convert_flask_to_fastapi(
        "sample_apps/flask_simple",
        [
            {
                "path": "/",
                "methods": ["GET"],
                "handler": "hello_world",
                "file": "app.py",
            }
        ],
    )

    assert conversion_plan["routes"] == [
        {
            "original_path": "/",
            "fastapi_path": "/",
            "methods": ["GET"],
            "handler": "hello_world",
            "converted_code": '@app.get("/")\ndef hello_world():\n    # TODO(migration): unsupported pattern\n    return render_template(\'index.html\')',
            "converted": False,
            "unsupported": ["render_template"],
        }
    ]


def test_convert_flask_to_fastapi_marks_redirect_and_url_for_as_unsupported(monkeypatch):
    handler_source = "\n".join(
        [
            "def go_home():",
            "    flash('saved')",
            "    return redirect(url_for('home'))",
        ]
    )
    handler_node = ast.parse(handler_source).body[0]

    def fake_build_handler_index(search_root, routes):
        return {("app.py", "go_home"): handler_node}

    monkeypatch.setattr(flask_to_fastapi, "_build_handler_index", fake_build_handler_index)

    conversion_plan = convert_flask_to_fastapi(
        "sample_apps/flask_simple",
        [
            {
                "path": "/go-home",
                "methods": ["POST"],
                "handler": "go_home",
                "file": "app.py",
            }
        ],
    )

    assert conversion_plan["routes"] == [
        {
            "original_path": "/go-home",
            "fastapi_path": "/go-home",
            "methods": ["POST"],
            "handler": "go_home",
            "converted_code": '@app.post("/go-home")\ndef go_home():\n    # TODO(migration): unsupported pattern\n    flash(\'saved\')\n    return redirect(url_for(\'home\'))',
            "converted": False,
            "unsupported": ["flash", "redirect", "url_for"],
        }
    ]


def test_convert_flask_to_fastapi_marks_request_files_and_context_usage_as_unsupported(monkeypatch):
    handler_source = "\n".join(
        [
            "def upload():",
            "    file = request.files.get('photo')",
            "    current_app.logger.info(g.user)",
            "    return jsonify({'filename': file.filename if file else None})",
        ]
    )
    handler_node = ast.parse(handler_source).body[0]

    def fake_build_handler_index(search_root, routes):
        return {("app.py", "upload"): handler_node}

    monkeypatch.setattr(flask_to_fastapi, "_build_handler_index", fake_build_handler_index)

    conversion_plan = convert_flask_to_fastapi(
        "sample_apps/flask_simple",
        [
            {
                "path": "/upload",
                "methods": ["POST"],
                "handler": "upload",
                "file": "app.py",
            }
        ],
    )

    assert conversion_plan["routes"] == [
        {
            "original_path": "/upload",
            "fastapi_path": "/upload",
            "methods": ["POST"],
            "handler": "upload",
            "converted_code": '@app.post("/upload")\ndef upload():\n    # TODO(migration): unsupported pattern\n    file = request.files.get(\'photo\')\n    current_app.logger.info(g.user)\n    return {\'filename\': file.filename if file else None}',
            "converted": False,
            "unsupported": ["request.files", "current_app usage", "g usage"],
        }
    ]


def test_convert_flask_to_fastapi_converts_jsonify_tuple_status_code(monkeypatch):
    handler_source = "\n".join(
        [
            "def create_user():",
            "    data = {'ok': True}",
            "    return jsonify(data), 201",
        ]
    )
    handler_node = ast.parse(handler_source).body[0]

    def fake_build_handler_index(search_root, routes):
        return {("app.py", "create_user"): handler_node}

    monkeypatch.setattr(flask_to_fastapi, "_build_handler_index", fake_build_handler_index)

    conversion_plan = convert_flask_to_fastapi(
        "sample_apps/flask_simple",
        [
            {
                "path": "/users",
                "methods": ["POST"],
                "handler": "create_user",
                "file": "app.py",
            }
        ],
    )

    assert conversion_plan["routes"] == [
        {
            "original_path": "/users",
            "fastapi_path": "/users",
            "methods": ["POST"],
            "handler": "create_user",
            "converted_code": '@app.post("/users")\ndef create_user():\n    data = {\'ok\': True}\n    return JSONResponse(content=data, status_code=201)',
            "converted": True,
            "unsupported": [],
        }
    ]


def test_convert_flask_to_fastapi_marks_unsupported_path_converters(monkeypatch):
    handler_source = "\n".join(
        [
            "def get_user(user_id):",
            '    return jsonify({"user_id": user_id})',
        ]
    )
    handler_node = ast.parse(handler_source).body[0]

    def fake_build_handler_index(search_root, routes):
        return {("app.py", "get_user"): handler_node}

    monkeypatch.setattr(flask_to_fastapi, "_build_handler_index", fake_build_handler_index)

    conversion_plan = convert_flask_to_fastapi(
        "sample_apps/flask_simple",
        [
            {
                "path": "/users/<custom:user_id>",
                "methods": ["GET"],
                "handler": "get_user",
                "file": "app.py",
            }
        ],
    )

    assert conversion_plan["routes"] == [
        {
            "original_path": "/users/<custom:user_id>",
            "fastapi_path": "/users/{user_id}",
            "methods": ["GET"],
            "handler": "get_user",
            "converted_code": '@app.get("/users/{user_id}")\ndef get_user(user_id: str):\n    # TODO(migration): unsupported pattern\n    return {\'user_id\': user_id}',
            "converted": False,
            "unsupported": ["path converter: custom"],
        }
    ]
