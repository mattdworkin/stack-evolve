# stack-evolve
Adaptive enterprise tech stack evaluation and automated Flask-to-FastAPI migration modeling platform.

## Project Setup
### Cloning repo
```bash
git clone https://github.com/mattdworkin/stack-evolve
```
### Requirements

- Python 3.9+ recommended

After cloning, install required dependencies:

```bash
python3 -m pip install typer pytest
```
## Project Structure
The project is organized into the following folders:
```bash
detector/   # Logic for detecting whether a repository uses Flask
analyzer/   # Code that analyzes Flask applications and extracts routes
converter/  # Converts analyzed Flask routes into FastAPI route definitions
report/     # Generates migration output artifacts and reports
tests/      # Unit tests
```
## Running the CLI

The CLI can be executed using Python.

### Detect a repository
```
python cli.py detect <repo_path>
```

Use this to test sample_application in repo:

```bash
python cli.py detect sample_apps/flask_simple
```

This command checks whether a repository/file imports Flask and reports whether it is a Flask application.

### Analyze a repository
```
python cli.py analyze <repo_path>
```

Use this to test sample_application in repo:

```bash
python cli.py analyze sample_apps/flask_simple
```

This command analyzes a Flask repository and outputs structured route information.

Analyzer output uses this shared contract:

```json
[
  {
    "path": "/users/<int:user_id>",
    "methods": ["GET"],
    "handler": "get_user",
    "file": "app.py"
  }
]
```

### Convert a Repository
```
python3 cli.py convert <repo_path> --out <output_directory>
```
Use this to test sample_application in repo:

```bash
python3 cli.py convert sample_apps/flask_simple --out out_fastapi
```
This command now runs the full pipeline:

```text
detect -> analyze -> convert -> generate -> report
```

It writes stage artifacts and generated output into the target directory. The CLI also prints stage logs:

```text
Detecting framework...
Extracting routes...
Converting routes...
Generating FastAPI app...
Generating report...
```

For the sample app, the output directory will contain:

```text
out_fastapi/
  detection.json
  analysis.json
  conversion_plan.json
  generation_summary.json
  main.py
  requirements.txt
  MIGRATION_REPORT.json
```

`main.py` is generated from routes where `route["converted"] == true`.
`requirements.txt` includes:

```text
fastapi
uvicorn[standard]
```

`main.py` starts with:

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()
```

When converted routes need optional query parameters, the generator also adds:

```python
from typing import Optional
```

You can run the generated app with:

```bash
cd out_fastapi
uvicorn main:app --reload
```

To test the non-Flask failure path:

```bash
python3 cli.py convert sample_apps/non_flask_simple/app.py --out out_fastapi
```

That command should exit with code `1`, write `detection.json`, and stop before analysis.

## Shared Interfaces

### Converter output

The converter returns route entries in this format:

```json
[
  {
    "original_path": "/users/<int:user_id>",
    "fastapi_path": "/users/{user_id}",
    "methods": ["GET"],
    "handler": "get_user",
    "converted_code": "@app.get(\"/users/{user_id}\")\ndef get_user(user_id: int):\n    return {\"user_id\": user_id}",
    "converted": true,
    "unsupported": []
  }
]
```

Current converter coverage includes:

- Flask route decorators like `@app.route("/users", methods=["GET"])` to `@app.get("/users")`
- Path parameter conversion like `/users/<int:id>` to `/users/{id}` with typed parameters when possible
- Tuple responses like `return jsonify(data), 201` to `JSONResponse(content=data, status_code=201)`
- `# TODO(migration): unsupported pattern` markers for patterns we do not fully support yet

### Migration report output

`MIGRATION_REPORT.json` uses this format:

```json
{
  "routes_detected": 2,
  "routes_converted": 1,
  "unsupported_patterns": ["request.form"],
  "unconverted_handlers": ["submit_form"]
}
```

## Running Tests

### Run the tests

From the root of the project directory, run:

```bash
python3 -m pytest
```

To run only the new convert pipeline tests:

```bash
python3 -m pytest tests/test_cli_convert.py
```

To run the CLI, generator, converter, and report tests together:

```bash
python3 -m pytest tests/test_cli_convert.py tests/test_generator.py tests/test_converter.py tests/test_migration_report.py
```
