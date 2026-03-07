# Implement for Checkpoint 2

from pathlib import Path
import ast

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

    # if no path, eror
    if not root.exists():
        raise FileNotFoundError(f"Path not found: {repo_path}")

    # if path is a file and it's a .py file, check it; if it's a directory, check all .py files in it
    py_files = [root] if root.is_file() and root.suffix == ".py" else list(root.rglob("*.py"))

    # for each .py file, parse it andf check for flask imports
    for py_file in py_files:
        try:
            # abstract syntax tree
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        
        # walk through the tree and check for imports of flask
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name == "flask" or alias.name.startswith("flask.") for alias in node.names):
                    print("This application is Flask.")
                    return True

            if isinstance(node, ast.ImportFrom):
                if node.module == "flask" or (node.module and node.module.startswith("flask.")):
                    print("This application is Flask.")
                    return True

    print("This application isn't Flask.")
    return False
