from typing import Annotated
from fastapi import Header, HTTPException
from app.environment import secret_key

async def get_key(authorization: Annotated[str | None, Header()] = None):
    if authorization != secret_key:
        raise HTTPException(status_code=400, detail="Secret Key invalid")