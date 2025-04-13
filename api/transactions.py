import time
from typing import Optional

import gotrue
from fastapi import APIRouter, HTTPException, Depends, Query

from backend.utils.deal import generate_transaction_no
from backend.utils.logger import get_logger
from ..core.security import get_current_user, verify_feature_signature
from ..db.supabase import supabase
from ..models.schemas import ResponseModel, TokenTransactionResponse, UseFeatureRequest, BalanceResponse, RechargeRequest

logs = get_logger()
router = APIRouter()


@router.post("/use", response_model=ResponseModel[TokenTransactionResponse])
async def use_feature(request: UseFeatureRequest,
                      timestamp: int = Query(...),
                      sign: str = Query(...),
                      current_user: gotrue.types.User = Depends(get_current_user)):
    """使用功能并扣除代币"""
    user_id = current_user.id
    if not user_id:
        logs.error('用户不存在')
        raise HTTPException(status_code=400, detail="用户不存在")

    logs.info(f"User {user_id} attempting to use feature {request.feature_key}")

    try:
        # 1. 时间戳验证
        current_time = int(time.time())
        if abs(current_time - timestamp) > 120:
            logs.error('请求已过期')
            raise HTTPException(status_code=400, detail="请求已过期")
        else:
            logs.info('请求时间正确')

        # # 2. 验证功能配置
        # feature_config = await get_feature_config(request.feature_key)
        # if not feature_config:
        #     raise HTTPException(status_code=400, detail="功能不存在")
        # if request.token_cost != feature_config.token_cost:
        #     raise HTTPException(status_code=400, detail="代币消耗金额不正确")
        #

        # 3. 验证签名
        if not verify_feature_signature(user_id=user_id, amount=request.token_cost, timestamp=timestamp, sign=sign, feature_key=request.feature_key):
            logs.error('签名验证失败')
            raise HTTPException(status_code=400, detail="签名验证失败")

        # 4. 生成交易ID
        order_id = generate_transaction_no("TT")
        logs.info(f"Transaction ID: {order_id}")

        # 5. 检查是否重复提交
        order_response = supabase.table("token_transactions")\
            .select("id")\
            .eq("order_id", order_id)\
            .execute()
            
        if order_response.data:
            logs.error('重复的请求')
            raise HTTPException(status_code=400, detail="重复的请求")
        logs.info('请求不重复')

        # 验证功能代币消耗是否在合理范围
        if request.token_cost <= 0:
            logs.error('无效的代币消耗')
            raise HTTPException(status_code=400, detail="无效的代币消耗")
        logs.info('代币消耗合理')
            
        total_cost = request.token_cost
        
        # 检查用户余额
        balance_response = supabase.table("user_tokens")\
            .select("balance")\
            .eq("user_id", user_id)\
            .execute()
        ba_data = balance_response.data
        logs.info(f'用户余额:{ba_data}')

        if not balance_response.data:
            logs.error('未找到用户代币信息')
            raise HTTPException(status_code=404, detail="未找到用户代币信息")

        current_balance = balance_response.data[0]["balance"]
        if current_balance < total_cost:
            logs.error('代币余额不足')
            raise HTTPException(status_code=400, detail="代币余额不足")

        # 在执行代币扣除之前添加日志
        logs.info(f"Executing token transaction for user {user_id}, amount: {total_cost}, feature: {request.feature_key}")

        # 使用存储过程执行代币扣除和记录
        response = supabase.rpc(
            'use_feature_transaction',
            {
                'p_user_id': user_id,
                'p_amount': -total_cost,
                'p_description': f'使用{request.feature_key}功能',
                'p_transaction_type': 1,
                'p_order_id': order_id,
                'p_feature_key': request.feature_key,
                'p_feature_count': 1
            }
        ).execute()
        logs.info('执行完成存储过程')

        if not response.data:
            logs.error('存储过程执行失败')
            raise HTTPException(status_code=400, detail="存储过程执行失败")
            
        if not response.data.get('success'):
            error_msg = response.data.get('error', '扣除代币失败')
            error_code = response.data.get('code', 'UNKNOWN_ERROR')
            logs.error(f"Transaction failed: {error_code} - {error_msg}")
            raise HTTPException(
                status_code=400, 
                detail=error_msg
            )

        result_data = response.data['data']
        logs.info(f"处理成功: {result_data}")
        
        return ResponseModel(
            message="success",
            data={
                "transaction_id": result_data['transaction_id'],  # 确保是整数类型
                "order_id": order_id,     # 业务流水号
                "balance_after": result_data['balance_after'],
                "amount": result_data['amount'],
                "description": f'使用{request.feature_key}功能'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logs.error(f"Failed to use feature: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_balance", response_model=ResponseModel[BalanceResponse])
async def get_balance(current_user: gotrue.types.User = Depends(get_current_user)):
    """获取用户当前代币余额"""
    user_id = current_user.id
    if not user_id:
        raise HTTPException(status_code=400, detail="用户不存在")
    logs.info(f"Current user ID: {user_id}")
    try:

        # 直接使用查询，认证已经通过 get_current_user 处理
        response = supabase.table("user_tokens")\
            .select('balance')\
            .eq('user_id', user_id)\
            .execute()
            
        logs.trace(f"Query response: {response}")
            
        if not response.data:
            raise HTTPException(status_code=400, detail="未找到用户代币信息")
        aa = response.data[0]
        return ResponseModel(
            message="success",
            data={
                "balance": aa['balance']
            }
        )
    except Exception as e:
        logs.error(f"Failed to get balance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="获取余额失败")


@router.get("/history")
async def get_transaction_history(
    current_user: gotrue.types.User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    transaction_type: Optional[int] = Query(None, ge=1, le=4),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取用户的代币交易历史"""
    try:
        user_id = current_user.id
        
        # 构建基础查询
        query = supabase.table('token_transactions') \
            .select('*', count='exact') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True)
            
        # 添加可选的过滤条件
        if transaction_type is not None:
            query = query.eq('transaction_type', transaction_type)
            
        if start_date:
            query = query.gte('created_at', start_date)
            
        if end_date:
            query = query.lte('created_at', end_date)
            
        # 添加分页
        start = (page - 1) * page_size
        end = start + page_size - 1
        query = query.range(start, end)
        
        # 执行查询
        response = query.execute()
        
        return ResponseModel(
            message="获取交易历史成功",
            data={
                "transactions": response.data,
                "total": response.count,
                "page": page,
                "page_size": page_size
            }
        )
    except Exception as e:
        logs.error(f"Failed to get transaction history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="获取交易历史失败")


@router.get("/statistics")
async def get_transaction_statistics(
    current_user: gotrue.types.User = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取用户的代币交易统计信息"""
    try:
        user_id = current_user.id
        
        # 构建统计查询
        query = supabase.rpc(
            'get_transaction_statistics',
            {
                'p_user_id': user_id,
                'p_start_date': start_date,
                'p_end_date': end_date
            }
        ).execute()
        
        if not query.data:
            return ResponseModel(
                message="获取统计信息成功",
                data={
                    "total_consumption": 0,
                    "total_recharge": 0,
                    "total_transactions": 0
                }
            )
            
        return ResponseModel(
            message="获取统计信息成功",
            data=query.data[0]
        )
    except HTTPException:
        raise
    except Exception as e:
        logs.error(f"Failed to get transaction statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="获取统计信息失败")


@router.post("/recharge", response_model=ResponseModel[TokenTransactionResponse])
async def recharge_tokens(
    request: RechargeRequest,
    order_id: str = Query(...),  # 外部订单号（可选）
    timestamp: int = Query(...),
    sign: str = Query(...),
    current_user: gotrue.types.User = Depends(get_current_user)
):
    """充值代币（需要签名验证）"""
    try:
        user_id = current_user.id
        if not user_id:
            logs.error(f"UserID: {user_id},用户不存在")
            raise HTTPException(status_code=400, detail="用户不存在")
        
        logs.info(f"User {user_id} attempting to recharge tokens, amount: {request.token_add}")
        
        # 1. 时间戳验证
        current_time = int(time.time())
        if abs(current_time - timestamp) > 300:
            logs.error("请求已过期")
            raise HTTPException(status_code=400, detail="请求已过期")
        logs.info("请求时间验证通过")
            
        # 2. 验证签名
        if not verify_feature_signature(
            user_id=user_id,
            amount=request.token_add,
            timestamp=timestamp,
            sign=sign,
            feature_key=f"recharge_{request.racharge_type}"  # 充值操作的特殊feature_key
        ):
            logs.error("签名验证失败")
            raise HTTPException(status_code=400, detail="签名验证失败")
        logs.info("签名验证通过")
            
        # 3. 验证充值金额是否在合理范围
        if request.token_add <= 0 or request.token_add > 10000:
            logs.error(f"无效的充值金额: {request.token_cost}")
            raise HTTPException(status_code=400, detail="无效的充值金额")
        logs.info("充值金额验证通过")
            
        # 4. 检查订单是否已存在
        order_response = supabase.table("token_transactions")\
            .select("id")\
            .eq("order_id", order_id)\
            .execute()
            
        if order_response.data:
            logs.error(f"重复的订单ID: {order_id}")
            raise HTTPException(status_code=400, detail="订单已存在")
        logs.info("订单ID验证通过")

        order_id = generate_transaction_no("RC")
        
        # 执行充值
        response = supabase.rpc(
            'record_token_transaction',
            {
                'p_user_id': user_id,
                'p_amount': request.token_add,
                'p_description': f'充值{request.token_add}代币',
                'p_transaction_type': 2,
                'p_order_id': order_id
            }
        ).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="充值失败")
            
        result = response.data
        if not result.get('success'):
            error_msg = result.get('error', '充值失败')
            error_code = result.get('code', 'UNKNOWN_ERROR')
            raise HTTPException(status_code=400, detail=error_msg)
            
        # 确保返回的数据包含所有必需字段
        transaction_data = result['data']
        transaction_data['description'] = f'充值{request.token_add}代币'  # 添加description字段
            
        return ResponseModel(
            message="充值成功",
            data=transaction_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logs.error(f"Failed to recharge tokens: {str(e)}")
        raise HTTPException(status_code=400, detail="充值失败")
