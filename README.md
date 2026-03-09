# stack-evolve
Adaptive enterprise tech stack evaluation and automated Flask-to-FastAPI migration modeling platform.

## Project Setup
### Cloning repo
```bash
git clone https://github.com/mattdworkin/stack-evolve
```
### Requirements

- Python 3.9+ recommended

After cloning, install required dependency:

```bash
pip install typer
```
## Project Structure
The project is organized into the following folders:
```bash
detector/   # Logic for detecting whether a repository uses Flask
analyzer/   # Code that analyzes Flask applications and extracts routes
converter/  # Future module for converting Flask code to FastAPI
report/     # Future module for generating migration reports
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
python cli.py convert <repo_path> --out <output_directory>
```
Use this to test sample_application in repo:

```bash
python cli.py convert sample_apps/flask_simple --out out_fastapi
```
This command will eventually convert supported Flask patterns into a FastAPI application and generate a migration report.

Currently, `convert` serves as a CLI placeholder to confirm the command interface is functioning.

## Running Tests (Placeholder)

The project includes a `tests/` directory intended for unit tests. At the moment, this test suite only contains placeholder tests to confirm that the testing setup is working correctly.

### Install pytest

If you do not already have pytest installed, install it with:

```bash
pip install pytest
```
### Run the tests

From the root of the project directory, run:

```bash
python -m pytest
```

Since the current tests are placeholders, they are only meant to verify that the testing framework is configured correctly. More meaningful tests will be added as the detector, analyzer, and converter modules are implemented.
