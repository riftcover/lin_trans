from fastapi import APIRouter, HTTPException

from backend.utils.logger import get_logger
from ..db.supabase import supabase
from ..models.schemas import UserSignUp, UserLogin, ResetPasswordRequest, ResponseModel

logs = get_logger()

router = APIRouter()


@router.post("/signup", response_model=ResponseModel)
async def sign_up(user_data: UserSignUp):
    try:
        logs.info(f"Attempting to register user: {user_data.email}")
        result = supabase.auth.sign_up({"email": user_data.email, "password": user_data.password})

        if not result.user:
            raise HTTPException(status_code=400, detail="用户创建失败")

        return ResponseModel(message="注册成功，请查收邮件完成验证", data={"user": {"id": result.user.id, "email": result.user.email}})
    except Exception as e:
        logs.error(f"Registration failed: {str(e)}", exc_info=True)
        if "User already registered" in str(e):
            raise HTTPException(status_code=400, detail="该邮箱已被注册")
        raise HTTPException(status_code=400, detail="注册失败，请稍后重试")


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    try:
        logs.info(f"Attempting to reset password for email: {data.email}")

        # 使用 Supabase 内置的密码重置功能
        result = supabase.auth.reset_password_email(email=data.email,  # 只发送重置密码邮件
        )

        logs.info(f"Password reset email sent to: {data.email}")
        return {"message": "重置密码邮件已发送，请查收邮件"}
    except Exception as e:
        logs.error(f"Failed to send reset password email: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="发送重置密码邮件失败")


# 添加一个新的路由来处理密码重置的确认
@router.post("/confirm-password-reset")
async def confirm_password_reset(data: ResetPasswordRequest):
    try:
        logs.info(f"Confirming password reset for email: {data.email}")

        # 验证重置密码的 token 并更新密码
        result = supabase.auth.verify_otp({"email": data.email, "token": data.verification_code, "type": "recovery", "new_password": data.new_password})

        logs.info(f"Password reset confirmed for email: {data.email}")
        return {"message": "密码重置成功"}
    except Exception as e:
        logs.error(f"Failed to confirm password reset: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="密码重置失败，请确认验证码是否正确")


@router.post("/login")
async def login(user_data: UserLogin):
    try:
        logs.info(f"Attempting login for email: {user_data.email}")

        # 使用 Supabase 进行登录认证
        result = supabase.auth.sign_in_with_password({"email": user_data.email, "password": user_data.password})

        # 获取用户信息和会话信息
        user = result.user
        session = result.session

        logs.info(f"Login successful for user: {user.email}")

        # 修改返回数据结构，确保与前端期望的格式一致
        return {"user": {"id": user.id, "email": user.email, },
            "session": {"access_token": session.access_token, "refresh_token": session.refresh_token, "expires_at": session.expires_at, }}
    except Exception as e:
        logs.error(f"Login failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="邮箱或密码错误")


@router.post("/logout")
async def logout():
    try:
        logs.info("User logging out")
        # Supabase 会自动处理 session 的清除
        result = supabase.auth.sign_out()
        return {"message": "退出登录成功"}
    except Exception as e:
        logs.error(f"Logout failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
