from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

RouteInfo = dict[str, Any]
ConversionPlan = dict[str, Any]

_FLASK_PATH_PARAM_RE = re.compile(
    r"<(?:(?P<converter>[a-zA-Z_][a-zA-Z0-9_]*):)?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)>"
)
_FASTAPI_DECORATOR_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}
_FLASK_TYPE_MAP = {
    "int": "int",
    "float": "float",
    "path": "str",
    "string": "str",
    "uuid": "str",
}


def convert_flask_to_fastapi(
    repo_path: str | Path,
    routes: list[RouteInfo],
) -> ConversionPlan:
    """Build a Flask-to-FastAPI conversion plan using the shared route contract."""

    source_root = Path(repo_path)
    search_root = source_root if source_root.is_dir() else source_root.parent
    handler_index = _build_handler_index(search_root, routes)

    converted_routes: list[RouteInfo] = []
    notes = [
        "Converted Flask route decorators into FastAPI route definitions.",
    ]
    uses_http_exception = False
    uses_json_response = False
    uses_optional = False

    for route in routes:
        handler_node = handler_index.get((route.get("file", ""), route["handler"]))
        converted_route = _convert_route(route, handler_node)
        converted_routes.append(converted_route)
        uses_http_exception = uses_http_exception or converted_route["uses_http_exception"]
        uses_json_response = uses_json_response or converted_route["uses_json_response"]
        uses_optional = uses_optional or converted_route["uses_optional"]
        notes.extend(converted_route["unsupported"])

    generated_app = _build_fastapi_app(
        converted_routes,
        uses_http_exception=uses_http_exception,
        uses_json_response=uses_json_response,
        uses_optional=uses_optional,
    )

    return {
        "source_repo": str(source_root),
        "route_count": len(converted_routes),
        "routes": [
            {
                "original_path": route["original_path"],
                "fastapi_path": route["fastapi_path"],
                "methods": route["methods"],
                "handler": route["handler"],
                "converted_code": route["converted_code"],
                "converted": route["converted"],
                "unsupported": route["unsupported"],
            }
            for route in converted_routes
        ],
        "notes": _unique_strings(notes),
        "generated_files": {
            "app.py": generated_app,
        },
    }


def _build_handler_index(search_root: Path, routes: list[RouteInfo]) -> dict[tuple[str, str], ast.FunctionDef | ast.AsyncFunctionDef]:
    handler_index: dict[tuple[str, str], ast.FunctionDef | ast.AsyncFunctionDef] = {}

    for relative_file_path in sorted({route.get("file") for route in routes if route.get("file")}):
        file_path = search_root / relative_file_path
        if not file_path.exists():
            continue

        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                handler_index[(relative_file_path, node.name)] = node

    return handler_index


def _convert_route(
    route: RouteInfo,
    handler_node: ast.FunctionDef | ast.AsyncFunctionDef | None,
) -> RouteInfo:
    fastapi_path, path_params, path_unsupported = _convert_flask_path(route["path"])
    query_params = _extract_query_params(handler_node)
    signature, uses_optional = _build_signature(handler_node, path_params, query_params)
    body_lines, body_unsupported, uses_http_exception, uses_json_response = _build_function_body(
        handler_node,
        query_params,
    )
    unsupported = _unique_strings(path_unsupported + body_unsupported)
    converted = not unsupported
    converted_code = _build_route_code(
        fastapi_path,
        route["methods"],
        route["handler"],
        signature,
        body_lines,
        isinstance(handler_node, ast.AsyncFunctionDef),
    )

    return {
        "original_path": route["path"],
        "fastapi_path": fastapi_path,
        "methods": route["methods"],
        "handler": route["handler"],
        "converted_code": converted_code,
        "converted": converted,
        "unsupported": unsupported,
        "uses_http_exception": uses_http_exception,
        "uses_json_response": uses_json_response,
        "uses_optional": uses_optional,
    }


def _convert_flask_path(flask_path: str) -> tuple[str, dict[str, str], list[str]]:
    unsupported: list[str] = []
    path_params: dict[str, str] = {}

    def _replace(match: re.Match[str]) -> str:
        converter = match.group("converter")
        param_name = match.group("name")
        if converter and converter not in _FLASK_TYPE_MAP:
            unsupported.append(f"path converter: {converter}")
        path_params[param_name] = _FLASK_TYPE_MAP.get(converter or "string", "str")
        return "{" + param_name + "}"

    return _FLASK_PATH_PARAM_RE.sub(_replace, flask_path), path_params, unsupported


def _extract_query_params(
    handler_node: ast.FunctionDef | ast.AsyncFunctionDef | None,
) -> list[dict[str, str | None]]:
    if handler_node is None:
        return []

    query_params: dict[str, dict[str, str | None]] = {}
    for node in ast.walk(handler_node):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue

        request_arg = _parse_request_args_get(node.value)
        if request_arg is None:
            continue

        query_key, default_value = request_arg
        param_name = node.targets[0].id
        query_params[param_name] = {
            "name": param_name,
            "query_key": query_key,
            "default": default_value,
        }

    return list(query_params.values())


def _build_signature(
    handler_node: ast.FunctionDef | ast.AsyncFunctionDef | None,
    path_params: dict[str, str],
    query_params: list[dict[str, str | None]],
) -> tuple[str, bool]:
    query_param_index = {param["name"]: param for param in query_params}
    signature_parts: list[str] = []
    uses_optional = False

    original_args: list[str] = []
    if handler_node is not None:
        original_args = [arg.arg for arg in handler_node.args.args]

    for arg_name in original_args:
        if arg_name in path_params:
            signature_parts.append(f"{arg_name}: {path_params[arg_name]}")
            continue

        if arg_name in query_param_index:
            signature_parts.append(_query_signature_part(query_param_index[arg_name]))
            uses_optional = True
            continue

        signature_parts.append(arg_name)

    for param_name, param in query_param_index.items():
        if param_name in original_args:
            continue
        signature_parts.append(_query_signature_part(param))
        uses_optional = True

    if handler_node is None:
        for param_name, param_type in path_params.items():
            signature_parts.append(f"{param_name}: {param_type}")

    return ", ".join(signature_parts), uses_optional


def _query_signature_part(query_param: dict[str, str | None]) -> str:
    default_value = query_param["default"] or "None"
    return f'{query_param["name"]}: Optional[str] = {default_value}'


def _build_function_body(
    handler_node: ast.FunctionDef | ast.AsyncFunctionDef | None,
    query_params: list[dict[str, str | None]],
) -> tuple[list[str], list[str], bool, bool]:
    if handler_node is None:
        return (
            [
                "    # TODO(migration): unsupported pattern",
                '    return {"status": "stub"}',
            ],
            ["missing handler body"],
            False,
            False,
        )

    transformer = _FlaskBodyTransformer(query_params)
    transformed_body: list[ast.stmt] = []
    for statement in handler_node.body:
        updated_statement = transformer.visit(statement)
        if updated_statement is None:
            continue
        if isinstance(updated_statement, list):
            transformed_body.extend(updated_statement)
            continue
        transformed_body.append(updated_statement)

    transformed_body = [ast.fix_missing_locations(statement) for statement in transformed_body]

    if not transformed_body:
        return (
            [
                "    # TODO(migration): unsupported pattern",
                '    return {"status": "stub"}',
            ],
            ["empty converted body"],
            transformer.uses_http_exception,
            transformer.uses_json_response,
        )

    body_lines: list[str] = []
    unsupported = list(transformer.issues)
    if unsupported:
        body_lines.append("    # TODO(migration): unsupported pattern")
    for statement in transformed_body:
        rendered_statement = ast.unparse(statement)
        body_lines.extend(_indent_lines(rendered_statement))

    return body_lines, unsupported, transformer.uses_http_exception, transformer.uses_json_response


def _indent_lines(block: str) -> list[str]:
    return [f"    {line}" if line else "" for line in block.splitlines()]


def _parse_request_args_get(node: ast.expr) -> tuple[str, str | None] | None:
    if not isinstance(node, ast.Call):
        return None
    if not isinstance(node.func, ast.Attribute):
        return None
    if node.func.attr != "get":
        return None
    if not isinstance(node.func.value, ast.Attribute):
        return None
    if node.func.value.attr != "args":
        return None
    if not isinstance(node.func.value.value, ast.Name):
        return None
    if node.func.value.value.id != "request":
        return None
    if not node.args:
        return None
    if not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
        return None

    default_node = node.args[1] if len(node.args) > 1 else None
    default_value = ast.unparse(default_node) if default_node is not None else None
    return node.args[0].value, default_value


def _extract_jsonify_payload(node: ast.expr | None) -> ast.expr | None:
    if not isinstance(node, ast.Call):
        return None
    if not isinstance(node.func, ast.Name) or node.func.id != "jsonify":
        return None
    if len(node.args) == 1 and not node.keywords:
        return node.args[0]
    if node.args:
        return None
    if not node.keywords:
        return None
    return ast.Dict(
        keys=[ast.Constant(keyword.arg) for keyword in node.keywords],
        values=[keyword.value for keyword in node.keywords],
    )


def _abort_exception_call(status_code: ast.expr) -> ast.Call:
    return ast.Call(
        func=ast.Name(id="HTTPException", ctx=ast.Load()),
        args=[],
        keywords=[ast.keyword(arg="status_code", value=status_code)],
    )


class _FlaskBodyTransformer(ast.NodeTransformer):
    def __init__(self, query_params: list[dict[str, str | None]]) -> None:
        self.query_params = {param["name"]: param for param in query_params}
        self.query_keys = {
            param["query_key"]: param["name"]
            for param in query_params
            if param["query_key"] is not None
        }
        self.uses_http_exception = False
        self.uses_json_response = False
        self.issues: list[str] = []

    def visit_Assign(self, node: ast.Assign) -> ast.Assign | None:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            request_arg = _parse_request_args_get(node.value)
            if request_arg is not None and node.targets[0].id in self.query_params:
                return None
        return self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> ast.stmt:
        abort_status = self._abort_status(node.value)
        if abort_status is not None:
            self.uses_http_exception = True
            return ast.copy_location(
                ast.Raise(exc=_abort_exception_call(abort_status), cause=None),
                node,
            )
        return self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> ast.Return:
        if node.value is None:
            return node

        tuple_response = self._tuple_json_response(node.value)
        if tuple_response is not None:
            payload, status_code = tuple_response
            self.uses_json_response = True
            return ast.copy_location(
                ast.Return(
                    value=ast.Call(
                        func=ast.Name(id="JSONResponse", ctx=ast.Load()),
                        args=[],
                        keywords=[
                            ast.keyword(arg="content", value=self.visit(payload)),
                            ast.keyword(arg="status_code", value=self.visit(status_code)),
                        ],
                    )
                ),
                node,
            )

        jsonify_payload = _extract_jsonify_payload(node.value)
        if jsonify_payload is not None:
            return ast.copy_location(ast.Return(value=self.visit(jsonify_payload)), node)

        return ast.copy_location(
            ast.Return(value=self.visit(node.value)),
            node,
        )

    def visit_Call(self, node: ast.Call) -> ast.expr:
        unsupported_pattern = self._unsupported_call_pattern(node)
        if unsupported_pattern is not None:
            self.issues.append(unsupported_pattern)
        request_arg = _parse_request_args_get(node)
        if request_arg is not None:
            query_key, _ = request_arg
            param_name = self.query_keys.get(query_key, query_key)
            return ast.copy_location(ast.Name(id=param_name, ctx=ast.Load()), node)
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id == "session":
            self.issues.append("session usage")
        return node

    def _abort_status(self, node: ast.expr) -> ast.expr | None:
        if not isinstance(node, ast.Call):
            return None
        if not isinstance(node.func, ast.Name) or node.func.id != "abort":
            return None
        if not node.args:
            self.issues.append("abort() without status code")
            return None
        return node.args[0]

    def _tuple_json_response(self, node: ast.expr) -> tuple[ast.expr, ast.expr] | None:
        if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
            return None
        jsonify_payload = _extract_jsonify_payload(node.elts[0])
        if jsonify_payload is None:
            return None
        return jsonify_payload, node.elts[1]

    def _unsupported_call_pattern(self, node: ast.Call) -> str | None:
        if isinstance(node.func, ast.Attribute):
            if (
                node.func.attr == "get"
                and isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == "form"
                and isinstance(node.func.value.value, ast.Name)
                and node.func.value.value.id == "request"
            ):
                return "request.form"
        return None


def _build_fastapi_app(
    routes: list[RouteInfo],
    *,
    uses_http_exception: bool,
    uses_json_response: bool,
    uses_optional: bool,
) -> str:
    lines: list[str] = []

    if uses_optional:
        lines.extend(
            [
                "from typing import Optional",
                "",
            ]
        )

    fastapi_imports = ["FastAPI"]
    if uses_http_exception:
        fastapi_imports.append("HTTPException")
    lines.append(f"from fastapi import {', '.join(fastapi_imports)}")

    if uses_json_response:
        lines.append("from fastapi.responses import JSONResponse")

    lines.extend(
        [
            "",
            'app = FastAPI(title="Migrated Flask App")',
        ]
    )

    if routes:
        for route in routes:
            lines.extend(["", route["converted_code"]])
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


def _route_decorator(path: str, methods: list[str]) -> str:
    if len(methods) == 1 and methods[0].lower() in _FASTAPI_DECORATOR_METHODS:
        return f'@app.{methods[0].lower()}("{path}")'
    return f'@app.api_route("{path}", methods={methods})'


def _build_route_code(
    path: str,
    methods: list[str],
    handler: str,
    signature: str,
    body_lines: list[str],
    is_async: bool,
) -> str:
    decorator = _route_decorator(path, methods)
    function_prefix = "async def" if is_async else "def"
    lines = [
        decorator,
        f"{function_prefix} {handler}({signature}):",
    ]
    lines.extend(body_lines)
    return "\n".join(lines)


def _unique_strings(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values
