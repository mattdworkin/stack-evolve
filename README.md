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
converter/  # Future module for converting Flask code to FastAPI
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
detector -> analyzer -> converter -> generator
```

It writes stage artifacts and generated output into the target directory. For the sample app, the output directory will contain:

```text
out_fastapi/
  detection.json
  analysis.json
  conversion_plan.json
  generation_summary.json
  app.py
  migration_report.json
```

To test the non-Flask failure path:

```bash
python3 cli.py convert sample_apps/non_flask_simple/app.py --out out_fastapi
```

That command should exit with code `1`, write `detection.json`, and stop before analysis.

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

To run the related detector, analyzer, and convert tests together:

```bash
python3 -m pytest tests/test_cli_convert.py tests/test_detector.py tests/test_route_analyzer.py
```
