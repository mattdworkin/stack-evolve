from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
def health():
    return {'ok': True}

@app.get("/users/{user_id}")
def get_user(user_id: int, q: Optional[str] = None):
    if user_id < 0:
        raise HTTPException(status_code=404)
    return JSONResponse(content={'user_id': user_id, 'q': q}, status_code=200)
