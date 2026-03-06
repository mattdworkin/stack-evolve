# File will be used later. To run tests, navigate to repo root and input: pytest


from detector.flask_detector import is_flask_app

def test_detects_flask_app():
    assert is_flask_app("sample_apps/flask_simple/app.py") is True
   

def test_rejects_non_flask_app():
    assert is_flask_app("sample_apps/non_flask_simple/app.py") is False
    
