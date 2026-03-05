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

### Analyze a repository
```
python cli.py analyze <repo_path>
```

Use this to test sample_application in repo:

```bash
python cli.py analyze sample_apps/flask_simple
```

This command will eventually analyze a repository to detect whether it is a Flask application and extract route information.

### Convert a Repository
```
python cli.py convert <repo_path> --out <output_directory>
```
Use this to test sample_application in repo:

```bash
python cli.py convert sample_apps/flask_simple --out out_fastapi
```
This command will eventually convert supported Flask patterns into a FastAPI application and generate a migration report.

Currently, both commands serve as CLI placeholders to confirm the command interface is functioning.
