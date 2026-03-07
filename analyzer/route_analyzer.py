from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


RouteInfo = dict[str, Any]


def analyze_flask_routes(repo_path: str | Path) -> list[RouteInfo]:
    """Extract Flask routes from a Python file or repository."""
    root_path = Path(repo_path)
    search_root = root_path if root_path.is_dir() else root_path.parent
    python_files = _collect_python_files(root_path)

    routes: list[RouteInfo] = []
    for file_path in python_files:
        routes.extend(_extract_file_routes(file_path, search_root))

    return routes


def _collect_python_files(root_path: Path) -> list[Path]:
    if root_path.is_file():
        return [root_path] if root_path.suffix == ".py" else []
    return sorted(root_path.rglob("*.py"))


def _extract_file_routes(file_path: Path, search_root: Path) -> list[RouteInfo]:
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    visitor = _FlaskRouteVisitor(_to_relative_path(file_path, search_root))
    visitor.visit(tree)
    return visitor.routes


def _to_relative_path(file_path: Path, search_root: Path) -> str:
    try:
        return file_path.relative_to(search_root).as_posix()
    except ValueError:
        return file_path.name


class _FlaskRouteVisitor(ast.NodeVisitor):
    def __init__(self, relative_file_path: str) -> None:
        self.relative_file_path = relative_file_path
        self.routes: list[RouteInfo] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._collect_routes(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._collect_routes(node)
        self.generic_visit(node)

    def _collect_routes(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for decorator in node.decorator_list:
            route_info = _parse_route_decorator(decorator)
            if route_info is None:
                continue

            self.routes.append(
                {
                    "path": route_info["path"],
                    "methods": route_info["methods"],
                    "handler": node.name,
                    "file": self.relative_file_path,
                }
            )


def _parse_route_decorator(decorator: ast.expr) -> dict[str, Any] | None:
    if not isinstance(decorator, ast.Call):
        return None
    if not isinstance(decorator.func, ast.Attribute):
        return None
    if decorator.func.attr != "route":
        return None

    path = _extract_path(decorator)
    if path is None:
        return None

    methods = _extract_methods(decorator)
    return {"path": path, "methods": methods or ["GET"]}


def _extract_path(decorator: ast.Call) -> str | None:
    if decorator.args:
        return _string_value(decorator.args[0])

    for keyword in decorator.keywords:
        if keyword.arg == "rule":
            return _string_value(keyword.value)

    return None


def _extract_methods(decorator: ast.Call) -> list[str] | None:
    methods_value = next(
        (keyword.value for keyword in decorator.keywords if keyword.arg == "methods"),
        None,
    )
    if methods_value is None:
        return None

    if isinstance(methods_value, ast.Constant) and isinstance(methods_value.value, str):
        return [methods_value.value.upper()]

    if not isinstance(methods_value, (ast.List, ast.Tuple, ast.Set)):
        return None

    methods: list[str] = []
    for element in methods_value.elts:
        method = _string_value(element)
        if method is None:
            return None
        methods.append(method.upper())

    return methods


def _string_value(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None
