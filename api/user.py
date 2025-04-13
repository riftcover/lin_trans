from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials

from backend.utils.logger import get_logger
from ..middleware.auth import verify_token, security
from ..models.schemas import ResponseModel

logger = get_logger()
router = APIRouter()

@router.get("/me", response_model=ResponseModel)
async def get_user_profile(request: Request):
    # 用户信息已经在中间件中验证并添加到request.state
    user = request.state.user

    return ResponseModel(
        message="获取用户信息成功",
        data={"user": {
            "id": user.id,
            "email": user.email,
            # 其他用户信息...
        }}
    )

# 或者使用 Depends 方式
@router.get("/profile", response_model=ResponseModel)
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = await verify_token(credentials)
    return ResponseModel(
        message="获取用户信息成功",
        data={"user": {
            "id": user.id,
            "email": user.email
        }}
    )