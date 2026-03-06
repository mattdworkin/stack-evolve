# File will be used later. To run tests, navigate to repo root and input: pytest

from detector.flask_detector import is_flask_app
from pathlib import Path 
import pytest

def test_detects_flask_app():
    """Verify the detector returns True for the local simple Flask sample app."""

    assert is_flask_app("sample_apps/flask_simple/app.py") is True
   

def test_rejects_non_flask_app():
    """Verify the detector returns False for the local simple non-Flask sample app."""

    assert is_flask_app("sample_apps/non_flask_simple/app.py") is False
    


@pytest.mark.integration
@pytest.mark.parametrize(
    "relative_parts, expected",
    [
        (["Project_Samples", "sample-flask"], True),
        (["Project_Samples", "FastAPI-app"], False),  
    ],
)

def test_detector_on_larger_repos(relative_parts, expected):
    """Validate detector behavior on larger external repos using relative paths."""

    repo_root = Path(__file__).resolve().parents[1]      # .../Project/stack-evolve
    target = repo_root.parent.parent                     # .../CS_4365
    repo_path = target.joinpath(*relative_parts)

    if not repo_path.exists():
        pytest.skip(f"Missing sample repo: {repo_path}")

    assert is_flask_app(str(repo_path)) is expected
