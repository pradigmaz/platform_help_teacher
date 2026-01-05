from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Response, Body, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_csrf_protect import CsrfProtect

from app.core import security
from app.core.config import settings
from app.core.limiter import limiter
from app.db.session import get_db
from app.core.redis import get_redis
from app.models import User

router = APIRouter()


@router.get("/csrf-token")
async def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    """Get CSRF token for frontend."""
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = JSONResponse(content={"csrf_token": csrf_token})
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("/otp")
@limiter.limit("5/minute")
async def login_with_otp(
    request: Request,
    response: Response,
    otp: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    csrf_protect: CsrfProtect = Depends()
) -> Any:
    """
    Обмен OTP кода на HttpOnly Cookie.
    """
    await csrf_protect.validate_csrf(request)
    
    telegram_id = await redis.get(f"auth:{otp}")
    
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    # Check if telegram_id is a valid integer
    if not telegram_id.isdigit():
        await redis.delete(f"auth:{otp}") # Cleanup bad data
        raise HTTPException(status_code=400, detail="Invalid data format")

    await redis.delete(f"auth:{otp}")
    
    result = await db.execute(select(User).where(User.social_id == int(telegram_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # FIX: Check if user is active
    if not user.is_active:
         raise HTTPException(status_code=403, detail="User is inactive")
        
    access_token = security.create_access_token(user.id)
    
    is_production = settings.ENVIRONMENT == "production"
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {"message": "Logged in successfully", "user": {"full_name": user.full_name, "role": user.role}}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"message": "Logged out"}