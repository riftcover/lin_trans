from fastapi import APIRouter, HTTPException

from backend.utils.logger import get_logger
from ..db.supabase import supabase

logs = get_logger()

router = APIRouter()

@router.get("")
async def get_features():
    """获取所有可用功能及其价格"""
    try:
        response = supabase.table('token_prices') \
            .select('*') \
            .eq('status', 1) \
            .execute()
        return response.data
    except Exception as e:
        logs.error(f"Failed to get features: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="获取功能列表失败")

