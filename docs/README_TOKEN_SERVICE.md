# 代币服务重构说明

## 概述

本次重构采用依赖注入与接口模式，将代币相关功能从工具类中分离出来，形成独立的服务。这种设计模式提高了代码的可维护性、可测试性和可扩展性。

## 文件结构

```
nice_ui/
├── interfaces/
│   ├── __init__.py
│   ├── auth.py           # 认证接口
│   ├── ui_manager.py     # UI管理器接口
│   └── token.py          # 代币服务接口（新增）
├── services/
│   ├── __init__.py
│   ├── auth_service.py   # 认证服务实现
│   ├── token_service.py  # 代币服务实现（新增）
│   └── service_provider.py # 服务提供者
└── managers/
    ├── __init__.py
    └── ui_manager.py     # UI管理器实现
```

## 主要组件

### 1. 接口

- `TokenServiceInterface`: 定义代币相关的方法，如获取余额、计算代币消耗、检查余额是否足够等

### 2. 服务实现

- `TokenService`: 实现代币服务接口，处理代币余额查询、消耗计算等功能

### 3. 服务提供者

- `ServiceProvider`: 负责创建和管理服务实例，提供获取服务的方法（已更新以支持代币服务）

## 使用方法

### 1. 获取代币服务

```python
from nice_ui.services.service_provider import ServiceProvider

# 获取代币服务
token_service = ServiceProvider().get_token_service()

# 获取用户余额
user_balance = token_service.get_user_balance()
print(f"当前代币余额: {user_balance}")

# 计算ASR任务所需代币
video_duration = 600  # 10分钟视频
asr_tokens = token_service.calculate_asr_tokens(video_duration)
print(f"ASR任务需要 {asr_tokens} 代币")

# 检查余额是否足够
if token_service.is_balance_sufficient(asr_tokens):
    print("余额足够，可以继续任务")
else:
    print("余额不足，需要充值")
    token_service.prompt_recharge_dialog()
```

### 2. 在现有代码中的应用

已经更新了以下文件以使用新的代币服务：

- `nice_ui/main_win/secwin.py`: 更新了`check_cloud_asr`方法
- `nice_ui/task/main_worker.py`: 更新了`cloud_asr_work`方法
- `nice_ui/util/tools.py`: 保留了兼容性方法，但内部使用新的代币服务

## 优势

1. **解耦**: 代币逻辑与其他逻辑分离，降低了代码耦合度
2. **可测试性**: 通过接口可以轻松模拟依赖进行单元测试
3. **可维护性**: 代码结构清晰，职责明确，易于维护
4. **可扩展性**: 可以轻松添加新的代币相关功能

## 注意事项

1. 服务是单例的，全局只有一个实例
2. 服务之间的依赖通过构造函数注入
3. 使用服务时，通过`ServiceProvider`获取，不要直接创建

## 后续优化建议

1. 实现更精确的代币消耗计算逻辑
2. 添加代币消耗历史记录功能
3. 实现实际的充值功能
4. 在UI上实时显示用户当前代币余额
