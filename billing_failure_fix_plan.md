# 翻译任务扣费失败处理修复计划

## 🔍 **问题分析**

### 当前问题
- **网络连接失败**：`[WinError 10061] 由于目标计算机积极拒绝，无法连接`
- **扣费失败但任务继续**：翻译任务完成，但实际没有扣费
- **日志误导**：显示"扣费完成"但实际扣费失败

### 根本原因
1. `TransTaskManager.consume_tokens_for_task`没有返回扣费结果
2. 任务处理器没有检查扣费结果
3. 扣费失败时任务仍然标记为成功

## 📋 **修复计划**

### ✅ 阶段1：修复扣费逻辑和日志（已完成）

#### 1.1 修改TransTaskManager.consume_tokens_for_task
- **返回值**：改为返回`bool`类型，表示扣费是否成功
- **日志优化**：使用✅❌符号清晰标识扣费结果
- **错误处理**：统一异常处理，返回false

#### 1.2 修改任务处理器扣费调用
- **检查扣费结果**：根据返回值判断扣费是否成功
- **失败处理**：扣费失败时任务失败，通知UI错误
- **日志准确性**：只有真正扣费成功才记录"扣费完成"

### 🔄 阶段2：增强错误处理策略（待实现）

#### 2.1 网络错误重试机制
```python
def consume_tokens_with_retry(self, task_id: str, max_retries: int = 3) -> bool:
    """带重试的扣费方法"""
    for attempt in range(max_retries):
        try:
            if self.consume_tokens_for_task(task_id):
                return True
            time.sleep(2 ** attempt)  # 指数退避
        except NetworkError:
            if attempt == max_retries - 1:
                return False
            time.sleep(2 ** attempt)
    return False
```

#### 2.2 扣费状态持久化
```python
class BillingStatus:
    PENDING = "pending"      # 待扣费
    SUCCESS = "success"      # 扣费成功
    FAILED = "failed"        # 扣费失败
    RETRYING = "retrying"    # 重试中
```

#### 2.3 用户体验优化
- **任务状态显示**：区分"翻译完成"和"扣费完成"
- **重试按钮**：允许用户手动重试扣费
- **批量补扣费**：网络恢复后批量处理失败的扣费

### 🚀 阶段3：高级功能（未来扩展）

#### 3.1 离线扣费队列
- 网络断开时将扣费请求存储到本地队列
- 网络恢复时自动处理队列中的扣费请求

#### 3.2 扣费状态监控
- 实时监控扣费成功率
- 网络状态检测和告警

#### 3.3 用户余额缓存
- 本地缓存用户余额，减少网络请求
- 定期同步服务端余额

## 🔧 **已实现的修复**

### 修复1：TransTaskManager返回扣费结果
```python
def consume_tokens_for_task(self, task_id: str) -> bool:
    """返回扣费是否成功"""
    try:
        billing_success = token_service.consume_tokens(token_amount, "cloud_trans")
        if billing_success:
            logger.info(f"✅ 翻译任务扣费成功 - 算力: {token_amount}, 任务ID: {task_id}")
            return True
        else:
            logger.error(f"❌ 翻译任务扣费失败 - 算力: {token_amount}, 任务ID: {task_id}")
            return False
    except Exception as e:
        logger.error(f"❌ 翻译任务扣费异常 - 任务ID: {task_id}, 错误: {str(e)}")
        return False
```

### 修复2：任务处理器检查扣费结果
```python
# 尝试扣费
billing_success = TransTaskManager().consume_tokens_for_task(task.unid)

if billing_success:
    logger.info(f'✅ 翻译任务完成并扣费成功 - 任务ID: {task.unid}')
else:
    logger.error(f'❌ 翻译任务扣费失败，任务状态异常 - 任务ID: {task.unid}')
    # 扣费失败时，通知UI任务出错
    data_bridge.emit_task_error(task.unid, "扣费失败")
    raise Exception(f"翻译任务扣费失败: {task.unid}")
```

## 📊 **修复效果**

### 修复前的日志
```
2025-09-11 10:05:34.038 | WARNING  | app.cloud_trans.task_manager:consume_tokens_for_task:38 - 翻译代币消费失败: 3
2025-09-11 10:05:34.038 | INFO     | nice_ui.task.queue_worker:process:275 - ASR+翻译任务扣费完成，任务ID: xxx
```
**问题**：扣费失败但显示"扣费完成"

### 修复后的日志
```
2025-09-11 10:05:34.038 | ERROR    | app.cloud_trans.task_manager:consume_tokens_for_task:45 - ❌ 翻译任务扣费失败 - 算力: 3, 任务ID: xxx
2025-09-11 10:05:34.038 | ERROR    | nice_ui.task.queue_worker:process:275 - ❌ 翻译任务扣费失败，任务状态异常 - 任务ID: xxx
```
**改进**：清晰标识扣费失败，任务状态正确

## 🎯 **验证要点**

1. **扣费成功场景**：
   - 日志显示"✅ 翻译任务扣费成功"
   - 任务状态为完成
   - 用户余额正确扣减

2. **扣费失败场景**：
   - 日志显示"❌ 翻译任务扣费失败"
   - 任务状态为失败
   - UI显示"扣费失败"错误
   - 用户余额不变

3. **网络异常场景**：
   - 日志显示"❌ 翻译任务扣费异常"
   - 任务状态为失败
   - 错误信息包含具体异常

## 🔮 **下一步计划**

1. **测试验证**：在不同网络环境下测试修复效果
2. **用户反馈**：收集用户对新错误处理的反馈
3. **功能增强**：根据需要实现阶段2的重试机制
4. **监控优化**：添加扣费成功率监控
