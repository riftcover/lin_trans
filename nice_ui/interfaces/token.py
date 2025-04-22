from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel, Field


class RechargePackage(BaseModel):
    """充值套餐数据结构"""
    price: int = Field(..., description="套餐价格(元)")
    token_amount: int = Field(..., description="代币数量")
class TokenServiceInterface(ABC):
    """代币服务接口，定义代币相关操作"""
    
    @abstractmethod
    def get_user_balance(self) -> int:
        """
        获取用户当前代币余额
        
        Returns:
            int: 用户当前代币余额，如果获取失败则返回0
        """
        pass
    
    @abstractmethod
    def calculate_asr_tokens(self, video_duration: float) -> int:
        """
        计算ASR任务所需代币
        
        Args:
            video_duration: 视频时长（秒）
            
        Returns:
            int: 所需代币数量
        """
        pass
    
    @abstractmethod
    def calculate_translation_tokens(self, word_count: int) -> int:
        """
        计算翻译任务所需代币
        
        Args:
            word_count: 单词数量
            
        Returns:
            int: 所需代币数量
        """
        pass
    
    @abstractmethod
    def is_balance_sufficient_with_value(self, required_tokens: int,balance: int) -> bool:
        """
        检查余额是否足够
        
        Args:
            required_tokens: 所需代币数量
            
        Returns:
            bool: 余额是否足够
        """
        pass
    
    @abstractmethod
    def prompt_recharge_dialog(self,required_tokens: int) -> bool:
        """
        弹出充值对话框并等待用户操作
        Args:
            required_tokens: 所需代币数量，默认为0
        
        Returns:
            bool: True表示充值成功或用户确认继续，False表示取消
        """
        pass

    @abstractmethod
    def get_recharge_packages(self) -> List[RechargePackage]:
        """
        获取充值套餐列表
        """
        pass
