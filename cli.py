import typer

app = typer.Typer(help="Flask -> FastAPI migration tool (MVP)")

@app.command()
def analyze(repo: str):
    """Analyze a repo (detect framework + list routes)."""
    typer.echo(f"[analyze] repo={repo}")
    # TODO: call detector + analyzer

@app.command()
def convert(repo: str, out: str = "out_fastapi"):
    """Convert a Flask repo to FastAPI (stub for now)."""
    typer.echo(f"[convert] repo={repo} out={out}")
    # TODO: call converter + generator/report later

if __name__ == "__main__":
    app()