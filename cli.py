import typer
import json
from pathlib import Path

from analyzer.route_analyzer import analyze_flask_routes
from converter.flask_to_fastapi import convert_flask_to_fastapi
from detector.flask_detector import is_flask_app
from report.migration_report import generate_fastapi_project, write_migration_report

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
    """Run the full migration pipeline and write migration artifacts."""
    _validate_repo_path(repo)

    repo_path = Path(repo)
    out_path = Path(out)
    out_path.mkdir(parents=True, exist_ok=True)

    typer.echo(f"[convert] repo={repo_path} out={out_path}")

    try:
        typer.echo("Detecting framework...")
        flask_detected = is_flask_app(str(repo_path))
        detection_payload = {
            "repo": str(repo_path),
            "is_flask_app": flask_detected,
        }
        _write_json(out_path / "detection.json", detection_payload)
        typer.echo(f"[convert] detection complete is_flask_app={flask_detected}")

        if not flask_detected:
            typer.echo("[convert] stopped: target does not appear to be a Flask app")
            raise typer.Exit(code=1)

        typer.echo("Extracting routes...")
        routes = analyze_flask_routes(repo_path)
        _write_json(out_path / "analysis.json", routes)
        typer.echo(f"[convert] analysis complete routes={len(routes)}")

        typer.echo("Converting routes...")
        conversion_plan = convert_flask_to_fastapi(repo_path, routes)
        _write_json(out_path / "conversion_plan.json", conversion_plan)
        typer.echo(
            "[convert] conversion complete "
            f"routes={len(conversion_plan.get('routes', []))}"
        )

        typer.echo("Generating FastAPI app...")
        generation_result = generate_fastapi_project(out_path, conversion_plan)
        _write_json(out_path / "generation_summary.json", generation_result)
        typer.echo(
            "[convert] generation complete "
            f"written_files={len(generation_result.get('written_files', []))}"
        )

        typer.echo("Generating report...")
        report_path = write_migration_report(
            out_path,
            analyzed_routes=routes,
            converted_routes=conversion_plan.get("routes", []),
        )
        typer.echo(f"[convert] report complete file={report_path.name}")
        typer.echo(f"[convert] pipeline complete output={out_path}")
    except typer.Exit:
        raise
    except Exception as exc:
        typer.echo(f"[convert] error: {exc}")
        raise typer.Exit(code=1)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

if __name__ == "__main__":
    app()
