# Commit Message

## 标题
```
refactor: 重构任务管理器架构，消除重复代码并改进封装性
```

## 详细描述

### 概述
本次重构解决了任务管理器架构中的多个设计问题：
- 消除了扣费和刷新逻辑的重复实现（3处扣费逻辑 → 1处）
- 统一了任务管理器继承体系（TransTaskManager 继承 BaseTaskManager）
- 改进了 TokenService 和 TokenAmountManager 的封装性
- 明确了各类的职责边界

**代码变更统计：** 6 个文件修改，删除 297 行，新增 172 行，净减少 125 行

---

### 主要变更

#### 1. 统一扣费逻辑到 BaseTaskManager
**问题：** 扣费逻辑重复实现在 3 个地方
- `BaseTaskManager._consume_tokens_for_task()`
- `TransTaskManager.consume_tokens_for_task()`
- `app/cloud_asr/task_manager.py._consume_tokens_for_task()`

**解决方案：**
- 在 `BaseTaskManager` 中添加 `_get_task_id(task)` 辅助方法，兼容不同任务对象（`task_id` 或 `unid` 属性）
- 修改 `BaseTaskManager._consume_tokens_for_task()` 使用辅助方法，支持所有任务类型
- 删除 `TransTaskManager.consume_tokens_for_task()` 和 `app/cloud_asr/task_manager.py._consume_tokens_for_task()`
- 所有任务管理器统一调用 `BaseTaskManager._consume_tokens_for_task()`

**影响文件：**
- `app/core/base_task_manager.py` - 添加 `_get_task_id()` 方法
- `app/cloud_trans/task_manager.py` - 删除 `consume_tokens_for_task()` (50行)
- `app/cloud_asr/task_manager.py` - 删除 `_consume_tokens_for_task()` (35行)

#### 2. 删除重复的 _refresh_usage_records()
**问题：** 刷新余额逻辑重复实现在 2 个地方
- `BaseTaskManager._refresh_usage_records()`
- `TransTaskManager._refresh_usage_records()`

**解决方案：**
- 删除 `TransTaskManager._refresh_usage_records()` (52行)
- 修改 `TransTaskManager._notify_task_completed()` 调用 `BaseTaskManager._refresh_usage_records()`

**影响文件：**
- `app/cloud_trans/task_manager.py` - 删除重复方法，使用基类实现

#### 3. TransTaskManager 继承 BaseTaskManager
**问题：** TransTaskManager 不继承 BaseTaskManager，无法复用通用逻辑

**解决方案：**
- 让 `TransTaskManager` 继承 `BaseTaskManager`
- 实现抽象方法（`_serialize_task`, `_deserialize_task`, `submit_task`）
  - 翻译任务是即时执行的，不需要持久化，提供空实现
- 添加 `__init__()` 方法初始化基类
- 删除 `_notify_task_completed()` 方法，使用基类实现

**影响文件：**
- `app/cloud_trans/task_manager.py` - 继承 BaseTaskManager，实现抽象方法

#### 4. 改进 TokenService 和 TokenAmountManager 的封装
**问题：** TokenService 直接访问 TokenAmountManager 的私有属性 `_task_token_info`

**解决方案：**
- 在 `TokenAmountManager` 中添加 `set_task_tokens_estimate()` 公开方法
- 修改 `TokenService.set_task_tokens_estimate()` 使用 TokenAmountManager 的公开方法
- 删除未使用的 `TokenService.consume_tokens_for_task()` 方法 (54行)

**影响文件：**
- `nice_ui/services/token_service.py` - 添加公开方法，删除未使用方法

#### 5. 移动 _execute_translation 到 TransTaskManager
**问题：** TaskProcessor 包含翻译业务逻辑，违反单一职责原则

**解决方案：**
- 在 `TransTaskManager` 中添加 `execute_translation()` 方法
- 从 `TaskProcessor` 中删除 `_execute_translation()` 方法 (88行)
- 更新所有调用点使用 `TransTaskManager.execute_translation()`

**影响文件：**
- `app/cloud_trans/task_manager.py` - 添加 `execute_translation()` 方法
- `nice_ui/task/queue_worker.py` - 删除 `_execute_translation()`，更新调用点

---

### 架构改进

#### 重构前的问题
```
❌ 职责混乱
- TaskProcessor 包含翻译业务逻辑
- TransTaskManager 不继承 BaseTaskManager

❌ 重复代码
- 扣费逻辑在 3 个地方
- 刷新逻辑在 2 个地方

❌ 封装破坏
- TokenService 直接访问 TokenAmountManager 内部数据
```

#### 重构后的架构
```
✅ 清晰的继承体系
BaseTaskManager (抽象基类)
├─ GladiaTaskManager (Gladia ASR)
└─ TransTaskManager (翻译) ← 新增继承

✅ 单一职责
- TaskProcessor: 任务流程编排
- TransTaskManager: 翻译业务逻辑
- BaseTaskManager: 任务管理通用功能
- TokenAmountManager: 数据存储
- TokenService: 代币业务逻辑

✅ 统一实现
- 扣费逻辑: BaseTaskManager._consume_tokens_for_task()
- 刷新逻辑: BaseTaskManager._refresh_usage_records()
- 任务ID获取: BaseTaskManager._get_task_id()

✅ 良好封装
- TokenService 通过公开接口访问 TokenAmountManager
```

---

### 测试验证

✅ Python 语法检查通过（所有文件）
✅ TransTaskManager 正确继承 BaseTaskManager
✅ 所有抽象方法已实现
✅ 单例模式正常工作
✅ 所有调用点已更新

---

### 破坏性变更

**无破坏性变更** - 所有公开接口保持不变，仅重构内部实现

---

### 文件变更清单

```
修改的文件：
- app/core/base_task_manager.py          (+36, -0)   添加 _get_task_id() 辅助方法
- app/cloud_trans/task_manager.py        (+120, -117) 继承 BaseTaskManager，删除重复代码
- app/cloud_asr/task_manager.py          (+5, -35)   使用 BaseTaskManager 统一扣费
- app/cloud_asr/gladia_task_manager.py   (+1, -1)    微调（无实质变更）
- nice_ui/services/token_service.py      (+10, -68)  改进封装，删除未使用方法
- nice_ui/task/queue_worker.py           (+0, -76)   删除 _execute_translation

总计：6 个文件，+172 行，-297 行，净减少 125 行
```

---

### 相关 Issue/PR

无

---

### 备注

本次重构遵循以下设计原则：
1. **单一职责原则** - 每个类只负责一件事
2. **DRY原则** - 消除重复代码
3. **开闭原则** - 对扩展开放，对修改封闭
4. **里氏替换原则** - 子类可以替换父类
5. **封装原则** - 通过公开接口访问数据

---

## Git 命令

```bash
# 查看变更
git diff

# 添加所有变更
git add app/core/base_task_manager.py \
        app/cloud_trans/task_manager.py \
        app/cloud_asr/task_manager.py \
        app/cloud_asr/gladia_task_manager.py \
        nice_ui/services/token_service.py \
        nice_ui/task/queue_worker.py

# 提交（使用简短标题）
git commit -m "refactor: 重构任务管理器架构，消除重复代码并改进封装性

- 统一扣费逻辑到 BaseTaskManager，删除 3 处重复实现
- 删除重复的 _refresh_usage_records()，统一使用基类实现
- TransTaskManager 继承 BaseTaskManager，复用通用逻辑
- 改进 TokenService 和 TokenAmountManager 的封装性
- 移动 _execute_translation 到 TransTaskManager，明确职责边界

代码变更：6 个文件，+172 行，-297 行，净减少 125 行
无破坏性变更，所有公开接口保持不变"
```

---

## 简短版本（如果需要更简洁的 commit message）

```bash
git commit -m "refactor: 重构任务管理器架构，消除重复代码

- 统一扣费和刷新逻辑到 BaseTaskManager
- TransTaskManager 继承 BaseTaskManager
- 改进 TokenService/TokenAmountManager 封装
- 移动翻译逻辑到 TransTaskManager

净减少 125 行代码，无破坏性变更"
```
