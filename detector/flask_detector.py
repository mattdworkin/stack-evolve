import ast
from pathlib import Path

def is_flask_app(repo_path: str) -> bool:
    """Detect whether a Python app/repository uses Flask imports via AST parsing.

    The function scans a single Python file or all ``.py`` files under a
    directory, parses each file with ``ast.parse``, and checks for import nodes
    that reference ``flask`` (for example ``import flask`` or
    ``from flask import Flask``).

    Args:
        repo_path: Path to a Python file or repository directory to inspect.

    Returns:
        True if any parsed file imports Flask; otherwise False.

    Raises:
        FileNotFoundError: If ``repo_path`` does not exist.
    """

    root = Path(repo_path)

    if not root.exists():
        raise FileNotFoundError(f"Path not found: {repo_path}")

    py_files = [root] if root.is_file() and root.suffix == ".py" else list(root.rglob("*.py"))

    for py_file in py_files:
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name == "flask" or alias.name.startswith("flask.") for alias in node.names):
                    return True

            if isinstance(node, ast.ImportFrom):
                if node.module == "flask" or (node.module and node.module.startswith("flask.")):
                    return True

    return False
