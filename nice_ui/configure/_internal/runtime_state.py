"""
运行时状态模块

管理应用程序的全局运行时状态。
"""
from queue import Queue
from typing import List, Dict, Any, Optional


class RuntimeState:
    """
    运行时状态管理器
    
    集中管理所有全局可变状态，避免散落的全局变量。
    """
    
    def __init__(self):
        # 队列相关
        self.queue_logs: Queue = Queue(1000)
        self.queuebox_logs: Queue = Queue(1000)
        self.lin_queue: Queue = Queue()
        
        # 任务队列
        self.queue_asr: List[str] = []
        self.queue_trans: List[str] = []
        self.queue_novice: Dict[str, str] = {}
        
        # 状态标志
        self.box_status: str = "stop"
        self.box_trans: str = "stop"
        self.separate_status: str = "stop"
        self.is_consuming: bool = False
        self.exit_soft: bool = False
        self.canceldown: bool = False
        
        # 计数器
        self.geshi_num: int = 0
        self.task_countdown: int = 60
        
        # 缓存
        self.video_cache: Dict[str, Any] = {}
        self.errorlist: Dict[str, Any] = {}
        
        # 其他状态
        self.last_opendir: str = ""
        self.video_codec: Optional[str] = None
        self.video_min_ms: int = 50
        
        # TTS 相关
        self.edgeTTS_rolelist: Optional[Any] = None
        self.AzureTTS_rolelist: Optional[Any] = None
        self.proxy: Optional[str] = None
        
        # 语音列表
        self.clone_voicelist: List[str] = ["clone"]
        self.ChatTTS_voicelist: List[str] = []
        self.openaiTTS_rolelist: str = "alloy,echo,fable,onyx,nova,shimmer"


# 创建全局单例
_runtime_state = RuntimeState()

