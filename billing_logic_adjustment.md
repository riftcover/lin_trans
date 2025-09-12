# 翻译任务扣费逻辑调整总结

## 🔍 **调整原因**

### 原有问题：
在`TranslationTaskProcessor`和`ASRTransTaskProcessor`中，扣费逻辑写在`finally`块中，导致：

1. **不合理的商业逻辑** - 翻译失败也会扣费
2. **用户体验差** - 用户为失败的服务付费
3. **逻辑不一致** - 与其他成功付费的服务不符

### 原有代码结构：
```python
try:
    translate_document(...)  # 翻译执行
except Exception as e:
    logger.error('翻译任务失败')
    raise e
finally:
    # ❌ 无论翻译成功失败都扣费
    billing_success = TransTaskManager().consume_tokens_for_task(task.unid)
```

## 🔧 **调整方案**

### 新的扣费逻辑：
**只有翻译成功后才扣费**

```python
try:
    translate_document(...)  # 翻译执行
    
    logger.info('翻译任务执行完成，开始扣费流程')
    
    # ✅ 翻译成功后才扣费
    token_service = ServiceProvider().get_token_service()
    token_amount = token_service.get_task_token_amount(task.unid, 0)
    
    if token_amount > 0:
        billing_success = TransTaskManager().consume_tokens_for_task(task.unid)
        
        if billing_success:
            logger.info('✅ 翻译任务完成并扣费成功')
        else:
            logger.error('❌ 翻译任务扣费失败')
            # 翻译成功但扣费失败，这是严重问题
            data_bridge.emit_task_error(task.unid, "翻译完成但扣费失败")
            raise Exception("翻译任务扣费失败")
    else:
        logger.info('✅ 翻译任务完成（无需扣费）')
        
except Exception as e:
    logger.error('翻译任务失败')
    # 翻译失败不扣费
    raise e
```

## 📋 **调整的文件和类**

### 1. TranslationTaskProcessor ✅
**文件**: `nice_ui/task/queue_worker.py`
**任务类型**: `WORK_TYPE.TRANS` (单独翻译任务)

**调整内容**:
- 将扣费逻辑从`finally`块移到`try`块内
- 只有`translate_document`成功执行后才进行扣费
- 扣费失败时抛出异常，任务失败

### 2. ASRTransTaskProcessor ✅
**文件**: `nice_ui/task/queue_worker.py`
**任务类型**: `WORK_TYPE.ASR_TRANS` (ASR+翻译组合任务)

**调整内容**:
- 将扣费逻辑从`finally`块移到`try`块内
- 只有翻译成功后才扣费
- 使用`new_task.unid`作为任务ID进行扣费

### 3. CloudASRTransTaskProcessor
**文件**: `nice_ui/task/queue_worker.py`
**任务类型**: `WORK_TYPE.CLOUD_ASR_TRANS` (云ASR+翻译任务)

**状态**: 已经是正确的逻辑，扣费在翻译成功后进行

## 🎯 **调整效果对比**

### 调整前：
```
翻译失败 → finally块执行 → 仍然扣费 ❌
翻译成功 → finally块执行 → 正常扣费 ✅
```

### 调整后：
```
翻译失败 → 异常抛出 → 不扣费 ✅
翻译成功 → 扣费逻辑执行 → 正常扣费 ✅
```

## 🔍 **扣费流程详解**

### 成功场景：
1. **翻译执行** → `translate_document()` 成功
2. **算力检查** → 获取任务算力 `token_amount`
3. **扣费执行** → 调用 `TransTaskManager().consume_tokens_for_task()`
4. **结果验证** → 检查扣费是否成功
5. **任务完成** → 记录成功日志

### 失败场景：
1. **翻译失败** → `translate_document()` 抛出异常
2. **异常处理** → 记录错误日志，通知UI
3. **任务失败** → 不执行扣费，任务标记为失败

### 扣费失败场景：
1. **翻译成功** → `translate_document()` 成功
2. **扣费失败** → 网络问题或余额不足
3. **任务失败** → 虽然翻译成功，但因扣费失败任务失败
4. **用户通知** → UI显示"翻译完成但扣费失败"

## 📊 **商业逻辑优化**

### 核心原则：
- **按结果付费** - 只为成功的服务收费
- **透明计费** - 用户清楚知道为什么被扣费
- **失败保护** - 服务失败不收费

### 用户体验改进：
- ✅ 翻译失败不会被扣费
- ✅ 扣费失败时用户能看到明确的错误信息
- ✅ 日志清晰显示扣费状态（✅❌符号）

## 🔮 **后续优化建议**

1. **扣费重试机制** - 网络临时故障时自动重试
2. **余额预检查** - 任务开始前检查余额是否充足
3. **扣费状态持久化** - 记录扣费状态，支持补扣费
4. **用户通知优化** - 更友好的错误提示和处理建议

## ✅ **验证要点**

测试以下场景确保调整正确：

1. **翻译成功 + 扣费成功** → 任务完成
2. **翻译成功 + 扣费失败** → 任务失败，显示扣费错误
3. **翻译失败** → 任务失败，不扣费
4. **算力为0** → 任务完成，不扣费
5. **网络异常** → 任务失败，不扣费

这样的调整确保了合理的商业逻辑和良好的用户体验。
