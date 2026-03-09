import typer
import json
from pathlib import Path

from analyzer.route_analyzer import analyze_flask_routes
from detector.flask_detector import is_flask_app

app = typer.Typer(help="Flask -> FastAPI migration tool (MVP)")

def _validate_repo_path(repo: str) -> None:
    if not Path(repo).exists():
        raise typer.BadParameter(f"Path not found: {repo}")


@app.command()
def detect(repo: str):
    """Detect whether the target repository/file is a Flask app."""
    _validate_repo_path(repo)
    flask_detected = is_flask_app(repo)

    typer.echo(f"[detect] repo={repo}")
    typer.echo(f"[detect] is_flask_app={flask_detected}")


@app.command()
def analyze(repo: str):
    """Analyze a Flask repo and output structured route data."""
    _validate_repo_path(repo)
    routes = analyze_flask_routes(repo)

    typer.echo(f"[analyze] repo={repo}")
    typer.echo(json.dumps(routes, indent=2))

@app.command()
def convert(repo: str, out: str = "out_fastapi"):
    """Convert a Flask repo to FastAPI (stub for now)."""
    typer.echo(f"[convert] repo={repo} out={out}")
    # TODO: call converter + generator/report later

if __name__ == "__main__":
    app()
