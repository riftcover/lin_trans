"""
任务管理器基类 - 提取所有任务管理器的共同功能

设计原则：
1. 消除重复代码 - 所有共同功能在基类中实现一次
2. 统一接口 - 所有任务管理器使用相同的通知和扣费逻辑
3. 简化维护 - 修改一次，所有子类受益
"""

import json
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List

from pydantic.json import pydantic_encoder

from nice_ui.configure.signal import data_bridge
from nice_ui.services.service_provider import ServiceProvider
from utils import logger
from utils.file_utils import write_segment_data_file


class BaseTaskManager(ABC):
    """
    任务管理器抽象基类
    
    提供所有任务管理器的共同功能：
    - 任务持久化（加载/保存）
    - 任务基本操作（创建/获取/更新）
    - UI通知（进度/完成/失败）
    - 代币扣费（统一回调机制）
    - Segment数据处理
    """
    
    def __init__(self, task_state_file: Path):
        """
        初始化基类
        
        Args:
            task_state_file: 任务状态文件路径
        """
        self.tasks: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.task_state_file = task_state_file
        
    # ==================== 任务持久化 ====================
    
    def _load_tasks(self) -> None:
        """从文件加载任务状态"""
        if not self.task_state_file.exists():
            return
            
        try:
            with open(self.task_state_file, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)
            
            with self.lock:
                loaded_count = 0
                for task_data in tasks_data:
                    try:
                        task = self._deserialize_task(task_data)
                        if task:
                            self.tasks[task.task_id] = task
                            loaded_count += 1
                    except Exception as e:
                        logger.error(f"加载任务数据失败: {str(e)}")
                
            logger.info(f"从文件加载了 {loaded_count} 个任务")
        except Exception as e:
            logger.error(f"加载任务状态失败: {str(e)}")
    
    def _save_tasks(self) -> None:
        """保存任务状态到文件"""
        try:
            with self.lock:
                tasks_data = []
                for task in self.tasks.values():
                    try:
                        task_dict = self._serialize_task(task)
                        tasks_data.append(task_dict)
                    except Exception as e:
                        logger.error(f"序列化任务数据失败: {str(e)}")
            
            # 确保目录存在
            self.task_state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存到文件
            with open(self.task_state_file, "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2, default=pydantic_encoder)
            
            logger.debug(f"成功保存 {len(tasks_data)} 个任务到文件")
            
        except Exception as e:
            logger.error(f"保存任务状态失败: {str(e)}")
    
    @abstractmethod
    def _serialize_task(self, task: Any) -> Dict[str, Any]:
        """
        序列化任务对象为字典（子类实现）
        
        Args:
            task: 任务对象
            
        Returns:
            Dict: 任务字典
        """
        pass
    
    @abstractmethod
    def _deserialize_task(self, task_data: Dict[str, Any]) -> Any:
        """
        从字典反序列化任务对象（子类实现）
        
        Args:
            task_data: 任务字典
            
        Returns:
            任务对象
        """
        pass
    
    # ==================== 任务基本操作 ====================
    
    def get_task(self, task_id: str) -> Optional[Any]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        with self.lock:
            return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs) -> None:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段
        """
        with self.lock:
            if task := self.tasks.get(task_id):
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                task.updated_at = time.time()
        
        self._save_tasks()
    
    # ==================== UI通知（统一实现） ====================
    
    def _notify_task_progress(self, task_id: str, progress: int) -> None:
        """
        通知UI任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度值（0-100）
        """
        try:
            if task_id:
                logger.info(f'更新任务进度，task_id: {task_id}, 进度: {progress}%')
                data_bridge.emit_whisper_working(task_id, progress)
        except Exception as e:
            logger.error(f"通知任务进度失败: {str(e)}")
    
    def _notify_task_completed(self, task_id: str) -> None:
        """
        通知UI任务完成，更新个人中心余额和历史记录
        
        注意：此方法应该在扣费成功后调用，确保余额是扣费后的最新值
        
        Args:
            task_id: 任务ID
        """
        try:
            if task_id:
                logger.info(f'更新任务完成状态，task_id: {task_id}')
                data_bridge.emit_whisper_finished(task_id)
                
                # 更新个人中心的余额和历史记录
                try:
                    # 获取代币服务
                    token_service = ServiceProvider().get_token_service()
                    
                    # 更新余额（异步方式，确保获取扣费后的最新余额）
                    def on_balance_success(result):
                        if result and 'data' in result:
                            balance = result['data'].get('balance', 0)
                            logger.info(f"获取扣费后余额成功: {balance}")
                            data_bridge.emit_update_balance(balance)
                        else:
                            logger.warning("获取余额失败或余额为0")
                    
                    def on_balance_error(error):
                        logger.error(f"获取余额失败: {error}")
                    
                    # 异步获取余额
                    from nice_ui.services.simple_api_service import simple_api_service
                    simple_api_service.get_balance(
                        callback_success=on_balance_success,
                        callback_error=on_balance_error
                    )
                    
                    # 更新历史记录（异步方式）
                    def on_history_success(result):
                        if result and 'data' in result:
                            transactions = result['data'].get('transactions', [])
                            logger.info(f"获取历史记录成功，记录数: {len(transactions)}")
                            data_bridge.emit_update_history(transactions)
                        else:
                            logger.warning("获取历史记录失败")
                    
                    def on_history_error(error):
                        logger.error(f"获取历史记录失败: {error}")
                    
                    # 异步获取历史记录
                    simple_api_service.get_history(
                        callback_success=on_history_success,
                        callback_error=on_history_error
                    )
                    
                except Exception as e:
                    logger.error(f"更新个人中心信息失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"通知任务完成失败: {str(e)}")
    
    def _notify_task_failed(self, task_id: str, error_message: str) -> None:
        """
        通知UI任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
        """
        try:
            if task_id:
                logger.info(f'通知任务失败，task_id: {task_id}, 错误: {error_message}')
                data_bridge.emit_task_error(task_id, error_message)
        except Exception as e:
            logger.error(f"通知任务失败失败: {str(e)}")
    
    # ==================== 代币扣费（统一实现） ====================
    
    def _consume_tokens_for_task(self, task: Any, feature_key: str, file_name: str) -> None:
        """
        为任务消费代币（统一回调机制）
        
        Args:
            task: 任务对象
            feature_key: 功能标识符（cloud_asr, cloud_trans等）
            file_name: 文件名
        """
        logger.info(f'消费代币 - 任务ID: {task.task_id}, 功能: {feature_key}')
        try:
            # 获取代币服务
            token_service = ServiceProvider().get_token_service()
            
            # 从代币服务中获取代币消费量
            token_amount = token_service.get_task_token_amount(task.task_id, 10)
            logger.info(f'从代币服务中获取代币消费量: {token_amount}, 任务ID: {task.task_id}')
            
            # 消费代币
            if token_amount > 0:
                logger.info(f"为任务消费代币: {token_amount}")
                
                # 定义扣费成功回调：只有在扣费真正完成后才更新余额
                def on_consume_success(result):
                    logger.info(f"代币消费成功: {token_amount}, 结果: {result}")
                    # 扣费成功后，更新个人中心余额和历史记录
                    self._notify_task_completed(task.task_id)
                
                def on_consume_error(error):
                    logger.warning(f"代币消费失败: {token_amount}, 错误: {error}")
                    # 即使扣费失败，也通知任务完成（但不更新余额）
                    data_bridge.emit_whisper_finished(task.task_id)
                
                # 异步消费代币，通过回调处理结果
                token_service.consume_tokens(
                    token_amount, feature_key, file_name,
                    callback_success=on_consume_success,
                    callback_error=on_consume_error
                )
            else:
                logger.warning("代币数量为0，不消费代币")
                # 无需扣费，直接通知完成
                self._notify_task_completed(task.task_id)
                
        except Exception as e:
            logger.error(f"消费代币时发生错误: {str(e)}")
            # 异常情况也要通知任务完成
            data_bridge.emit_whisper_finished(task.task_id)
    
    # ==================== Segment数据处理（统一实现） ====================
    
    def _create_segment_data_file(self, segments: List, audio_file: str) -> str:
        """
        创建segment_data文件
        
        Args:
            segments: segment数据列表
            audio_file: 音频文件路径
            
        Returns:
            str: segment_data文件路径
        """
        audio_path = Path(audio_file)
        segment_data_path = audio_path.with_name(f"{audio_path.stem}_segment_data.json")
        write_segment_data_file(segments, str(segment_data_path))
        logger.info(f"已创建segment_data文件: {segment_data_path}")
        return str(segment_data_path)
    
    def _save_segment_data_path(self, segment_data_path: str, audio_file: str, language: str) -> None:
        """
        保存segment_data路径信息，供UI智能分句功能使用
        
        Args:
            segment_data_path: segment_data文件路径
            audio_file: 音频文件路径
            language: 语言代码
        """
        # 创建一个元数据文件来保存segment_data路径
        audio_path = Path(audio_file)
        metadata_path = audio_path.with_name(f"{audio_path.stem}_metadata.json")
        metadata = {
            'segment_data_path': segment_data_path,
            'created_time': time.time(),
            'audio_file': audio_file,
            'language': language
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已保存segment_data路径信息: {metadata_path}，语言: {language}")
    
    # ==================== 抽象方法（子类必须实现） ====================
    
    @abstractmethod
    def submit_task(self, task_id: str) -> None:
        """
        提交任务（子类实现具体逻辑）
        
        Args:
            task_id: 任务ID
        """
        pass

