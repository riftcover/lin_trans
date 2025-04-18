# 认证服务重构说明

## 概述

本次重构采用依赖注入与接口模式，将认证相关功能从工具类中分离出来，形成独立的服务。这种设计模式提高了代码的可维护性、可测试性和可扩展性。

## 文件结构

```
nice_ui/
├── interfaces/           # 接口定义
│   ├── __init__.py
│   ├── auth.py           # 认证接口
│   └── ui_manager.py     # UI管理器接口
├── services/             # 服务实现
│   ├── __init__.py
│   ├── auth_service.py   # 认证服务实现
│   └── service_provider.py # 服务提供者
└── managers/             # 管理器实现
    ├── __init__.py
    └── ui_manager.py     # UI管理器实现
```

## 主要组件

### 1. 接口

- `AuthInterface`: 定义认证相关的方法，如检查登录状态、显示登录对话框等
- `UIManagerInterface`: 定义UI相关的方法，如显示登录窗口、显示消息提示等

### 2. 服务实现

- `AuthService`: 实现认证接口，处理登录状态检查和管理
- `MainUIManager`: 实现UI管理器接口，处理UI相关操作

### 3. 服务提供者

- `ServiceProvider`: 负责创建和管理服务实例，提供获取服务的方法

## 使用方法

### 1. 获取认证服务

```python
from nice_ui.services.service_provider import ServiceProvider

# 获取认证服务
auth_service = ServiceProvider().get_auth_service()

# 检查登录状态
if auth_service.check_login_status():
    # 用户已登录，继续处理
    pass
else:
    # 用户未登录，已经显示了登录对话框
    pass
```

### 2. 获取UI管理器

```python
from nice_ui.services.service_provider import ServiceProvider

# 获取UI管理器
ui_manager = ServiceProvider().get_ui_manager()

# 显示消息提示
ui_manager.show_message("成功", "操作已完成", "success")
```

## 优势

1. **解耦**: 认证逻辑与UI逻辑分离，降低了代码耦合度
2. **可测试性**: 通过接口可以轻松模拟依赖进行单元测试
3. **可维护性**: 代码结构清晰，职责明确，易于维护
4. **可扩展性**: 可以轻松添加新的认证方式或UI实现

## 注意事项

1. 服务是单例的，全局只有一个实例
2. 服务之间的依赖通过构造函数注入
3. 使用服务时，通过`ServiceProvider`获取，不要直接创建
