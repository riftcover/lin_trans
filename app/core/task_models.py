"""
任务数据模型

设计原则：
1. 数据属于任务 - Task 对象拥有代币数据
2. 聚合根 - Task 是聚合根，拥有完整的数据
3. 值对象 - TaskTokens 是不可变的值对象
4. 封装 - 通过方法操作数据，不直接暴露字段
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import time


@dataclass
class TaskTokens:
    """
    任务代币信息（值对象）
    
    设计原则：
    - 不可变性：通过方法返回新对象，确保线程安全
    - 防御性编程：确保代币非负
    - 单一职责：只负责代币数据
    """
    asr_tokens: int = 0
    trans_tokens: int = 0
    
    def __post_init__(self):
        """确保代币非负"""
        object.__setattr__(self, 'asr_tokens', max(0, self.asr_tokens))
        object.__setattr__(self, 'trans_tokens', max(0, self.trans_tokens))
    
    @property
    def total(self) -> int:
        """总代币"""
        return self.asr_tokens + self.trans_tokens
    
    def with_asr_tokens(self, tokens: int) -> 'TaskTokens':
        """
        返回新的 TaskTokens 对象，设置 ASR 代币
        
        Args:
            tokens: ASR 代币数量
            
        Returns:
            新的 TaskTokens 对象
        """
        return TaskTokens(asr_tokens=max(0, tokens), trans_tokens=self.trans_tokens)
    
    def with_trans_tokens(self, tokens: int) -> 'TaskTokens':
        """
        返回新的 TaskTokens 对象，设置翻译代币
        
        Args:
            tokens: 翻译代币数量
            
        Returns:
            新的 TaskTokens 对象
        """
        return TaskTokens(asr_tokens=self.asr_tokens, trans_tokens=max(0, tokens))
    
    def to_dict(self) -> Dict[str, int]:
        """序列化为字典"""
        return {
            'asr_tokens': self.asr_tokens,
            'trans_tokens': self.trans_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'TaskTokens':
        """从字典反序列化"""
        return cls(
            asr_tokens=data.get('asr_tokens', 0),
            trans_tokens=data.get('trans_tokens', 0)
        )


@dataclass
class Task:
    """
    任务对象（聚合根）
    
    设计原则：
    - 聚合根：拥有完整的数据（包括代币）
    - 封装：通过方法操作代币，不直接暴露字段
    - 单一数据源：代币数据只在这里
    
    注意：代币属于任务对象！删除任务自动删除代币。
    """
    task_id: str
    audio_file: str
    language: str
    status: str = "pending"
    
    # 代币信息属于任务！
    tokens: TaskTokens = field(default_factory=TaskTokens)
    
    # 元数据
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # 可选字段
    audio_url: Optional[str] = None
    result_url: Optional[str] = None
    error: Optional[str] = None
    progress: int = 0
    
    def set_asr_tokens(self, tokens: int) -> None:
        """
        设置 ASR 代币
        
        Args:
            tokens: ASR 代币数量
        """
        self.tokens = self.tokens.with_asr_tokens(tokens)
        self.updated_at = time.time()
    
    def set_trans_tokens(self, tokens: int) -> None:
        """
        设置翻译代币
        
        Args:
            tokens: 翻译代币数量
        """
        self.tokens = self.tokens.with_trans_tokens(tokens)
        self.updated_at = time.time()
    
    def get_total_tokens(self) -> int:
        """
        获取总代币
        
        Returns:
            总代币数量
        """
        return self.tokens.total
    
    def get_asr_tokens(self) -> int:
        """
        获取 ASR 代币
        
        Returns:
            ASR 代币数量
        """
        return self.tokens.asr_tokens
    
    def get_trans_tokens(self) -> int:
        """
        获取翻译代币
        
        Returns:
            翻译代币数量
        """
        return self.tokens.trans_tokens
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            任务数据字典
        """
        return {
            'task_id': self.task_id,
            'audio_file': self.audio_file,
            'language': self.language,
            'status': self.status,
            'tokens': self.tokens.to_dict(),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'audio_url': self.audio_url,
            'result_url': self.result_url,
            'error': self.error,
            'progress': self.progress
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        从字典反序列化
        
        Args:
            data: 任务数据字典
            
        Returns:
            Task 对象
        """
        tokens_data = data.get('tokens', {})
        return cls(
            task_id=data['task_id'],
            audio_file=data['audio_file'],
            language=data['language'],
            status=data.get('status', 'pending'),
            tokens=TaskTokens.from_dict(tokens_data),
            created_at=data.get('created_at', time.time()),
            updated_at=data.get('updated_at', time.time()),
            audio_url=data.get('audio_url'),
            result_url=data.get('result_url'),
            error=data.get('error'),
            progress=data.get('progress', 0)
        )

