import ast
import json
from pathlib import Path

from typer.testing import CliRunner

from cli import app


runner = CliRunner()


def test_convert_runs_full_pipeline_and_writes_artifacts():
    repo_root = Path(__file__).resolve().parents[1]
    sample_app_path = repo_root / "sample_apps" / "flask_simple"

    with runner.isolated_filesystem():
        output_dir = Path("out_fastapi")
        result = runner.invoke(app, ["convert", str(sample_app_path), "--out", str(output_dir)])

        assert result.exit_code == 0
        assert "Detecting framework..." in result.stdout
        assert "Extracting routes..." in result.stdout
        assert "Converting routes..." in result.stdout
        assert "Generating FastAPI app..." in result.stdout
        assert "Generating report..." in result.stdout
        assert "[convert] analysis complete routes=2" in result.stdout
        assert "[convert] generation complete written_files=2" in result.stdout
        assert "[convert] report complete file=MIGRATION_REPORT.json" in result.stdout

        detection = json.loads((output_dir / "detection.json").read_text(encoding="utf-8"))
        analysis = json.loads((output_dir / "analysis.json").read_text(encoding="utf-8"))
        conversion = json.loads((output_dir / "conversion_plan.json").read_text(encoding="utf-8"))
        generation = json.loads((output_dir / "generation_summary.json").read_text(encoding="utf-8"))
        migration_report = json.loads((output_dir / "MIGRATION_REPORT.json").read_text(encoding="utf-8"))
        generated_app = (output_dir / "main.py").read_text(encoding="utf-8")
        requirements = (output_dir / "requirements.txt").read_text(encoding="utf-8")

        assert detection["is_flask_app"] is True
        assert len(analysis) == 2
        assert conversion["route_count"] == 2
        assert generation["written_files"] == ["main.py", "requirements.txt"]
        assert migration_report == {
            "routes_detected": 2,
            "routes_converted": 2,
            "unsupported_patterns": [],
            "unconverted_handlers": [],
        }
        assert "from fastapi import FastAPI, HTTPException" in generated_app
        assert "from fastapi.responses import JSONResponse" in generated_app
        assert "@app.get(\"/health\")" in generated_app
        assert "@app.get(\"/users/{user_id}\")" in generated_app
        assert "def get_user(user_id: int, q: Optional[str] = None):" in generated_app
        assert "raise HTTPException(status_code=404)" in generated_app
        assert "JSONResponse" in generated_app
        assert "fastapi" in requirements
        assert "uvicorn[standard]" in requirements
        ast.parse(generated_app)


def test_convert_fails_for_non_flask_app():
    repo_root = Path(__file__).resolve().parents[1]
    sample_app_path = repo_root / "sample_apps" / "non_flask_simple" / "app.py"

    with runner.isolated_filesystem():
        output_dir = Path("out_non_flask")
        result = runner.invoke(app, ["convert", str(sample_app_path), "--out", str(output_dir)])

        assert result.exit_code == 1
        assert "[convert] stopped: target does not appear to be a Flask app" in result.stdout
        assert (output_dir / "detection.json").exists()
        assert not (output_dir / "analysis.json").exists()
