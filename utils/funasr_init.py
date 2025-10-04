"""
FunASR 初始化模块
确保所有必要的模型类在程序启动时被正确注册
"""

import sys
from utils import logger


def force_import_funasr_models():
    """
    强制导入所有 FunASR 模型类，确保注册机制正常工作
    这个函数应该在程序启动时调用一次
    """
    logger.info("开始强制导入 FunASR 模型类...")
    
    # 需要强制导入的模型模块列表
    model_modules = [
        'funasr.models.paraformer.bi_cif_paraformer',
        'funasr.models.paraformer.paraformer', 
        'funasr.models.sense_voice.model',
        'funasr.models.fsmn_vad.model',
        'funasr.models.ct_transformer.model',
        'funasr.models.campplus.model',
        'funasr.utils.postprocess_utils',
    ]
    
    imported_count = 0
    failed_count = 0
    
    for module_name in model_modules:
        try:
            __import__(module_name)
            imported_count += 1
            logger.trace(f"成功导入: {module_name}")
        except ImportError as e:
            failed_count += 1
            logger.warning(f"导入失败: {module_name} - {e}")
        except Exception as e:
            failed_count += 1
            logger.error(f"导入异常: {module_name} - {e}")
    
    logger.info(f"FunASR 模型导入完成: 成功 {imported_count}, 失败 {failed_count}")
    
    # 验证注册状态
    try:
        from funasr.register import tables
        registered_models = list(tables.model_classes.keys()) if hasattr(tables, 'model_classes') else []
        logger.info(f"已注册的模型类: {registered_models}")
        
        # 检查关键模型是否注册成功
        critical_models = ['BiCifParaformer', 'SenseVoiceSmall']
        for model in critical_models:
            if model in registered_models:
                logger.info(f"✅ 关键模型 {model} 注册成功")
            else:
                logger.warning(f"❌ 关键模型 {model} 未注册")
                
    except Exception as e:
        logger.error(f"无法验证模型注册状态: {e}")


def init_funasr():
    """
    FunASR 完整初始化函数
    包括模型导入和环境设置
    """
    # 设置环境变量
    import os
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    
    # 强制导入模型类
    force_import_funasr_models()
    
    logger.info("FunASR 初始化完成")


# 如果作为模块导入，自动执行初始化
if __name__ != "__main__":
    # 只在非主程序运行时自动初始化
    # 避免在测试或其他场景下意外执行
    pass
