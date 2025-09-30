# 架构模式与设计原则

## 核心架构模式

### 1. 依赖注入（Dependency Injection）
项目使用依赖注入模式来管理服务依赖关系。

**实现位置**: `nice_ui/services/service_provider.py`

**核心组件**:
- `ServiceProvider`: 单例服务提供者
- 通过构造函数注入依赖
- 全局只有一个服务实例

**使用示例**:
```python
from nice_ui.services.service_provider import ServiceProvider

# 获取认证服务
auth_service = ServiceProvider().get_auth_service()

# 获取UI管理器
ui_manager = ServiceProvider().get_ui_manager()
```

**优势**:
- 降低耦合度
- 提高可测试性
- 便于模拟依赖进行单元测试

### 2. 接口抽象（Interface Abstraction）
使用接口定义契约，实现与具体实现解耦。

**接口定义位置**: `nice_ui/interfaces/`
- `AuthInterface`: 认证接口
- `UIManagerInterface`: UI管理器接口
- `TokenInterface`: Token管理接口

**实现位置**: `nice_ui/services/` 和 `nice_ui/managers/`

**优势**:
- 代码结构清晰
- 职责明确
- 易于扩展和替换实现

### 3. 任务队列模式（Task Queue Pattern）
使用队列处理异步任务，避免阻塞UI线程。

**实现位置**: `nice_ui/task/`
- `main_worker.py`: 主工作线程
  - `Worker`: 工作线程基类
  - `QueueConsumer`: 队列消费者
  - `TaskHandler`: 任务处理器基类
  - `ASRTaskHandler`: ASR任务处理器
  - `TransTaskHandler`: 翻译任务处理器
  - `CloudASRTaskHandler`: 云端ASR任务处理器

**工作流程**:
1. UI线程将任务放入队列
2. 工作线程从队列取出任务
3. 任务处理器执行具体任务
4. 通过信号通知UI线程结果

**优势**:
- UI响应流畅
- 任务并发处理
- 错误隔离

### 4. 信号槽机制（Signal-Slot Pattern）
Qt的信号槽机制实现组件间通信。

**实现位置**: 
- `nice_ui/configure/signal.py`: 信号定义
- `nice_ui/ui/SingalBridge.py`: 信号桥接

**使用场景**:
- UI事件响应
- 线程间通信
- 组件解耦

**示例**:
```python
@Slot(str, dict)
def _on_data_received(self, endpoint_name: str, result: dict):
    """接收API数据"""
    pass

# 连接信号
self.api_worker.signals.data_received.connect(self._on_data_received)
```

### 5. ORM模式（Object-Relational Mapping）
使用SQLAlchemy管理数据库操作。

**实现位置**: `orm/`
- `queries.py`: 数据库查询封装（如 `PromptsOrm`）
- `linlin.db`: SQLite数据库

**优势**:
- 对象化数据操作
- 数据库无关性
- 自动处理SQL注入

### 6. 工厂模式（Factory Pattern）
用于创建对象实例。

**实现位置**: `nice_ui/task/orm_factory.py`

**用途**: 创建ORM实例和任务处理器

### 7. 适配器模式（Adapter Pattern）
适配不同的服务接口。

**实现位置**: `agent/srt_translator_adapter.py`

**用途**: 将翻译服务适配到SRT字幕格式

## 设计原则

### 1. 单一职责原则（Single Responsibility）
每个类/模块只负责一个功能。

**示例**:
- `AuthService`: 只负责认证
- `TokenService`: 只负责Token管理
- `UIManager`: 只负责UI操作

### 2. 开闭原则（Open-Closed）
对扩展开放，对修改封闭。

**实现**:
- 通过接口定义行为
- 通过继承扩展功能
- 使用配置文件控制行为

### 3. 依赖倒置原则（Dependency Inversion）
依赖抽象而不是具体实现。

**实现**:
- 依赖接口而不是具体类
- 通过ServiceProvider注入依赖

### 4. 接口隔离原则（Interface Segregation）
接口应该小而专注。

**实现**:
- `AuthInterface`: 只包含认证相关方法
- `TokenInterface`: 只包含Token相关方法

## 关键技术决策

### 1. 多进程处理
**决策**: 使用 `multiprocessing` 处理计算密集型任务

**原因**:
- Python GIL限制
- ASR和翻译是CPU密集型任务
- 需要真正的并行处理

**实现**:
```python
# macOS特殊处理
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

multiprocessing.freeze_support()
```

### 2. 配置管理
**决策**: 使用YAML配置文件 + 环境变量

**配置文件**: `config/api_config.yaml`

**环境支持**:
- development: 开发环境
- test: 测试环境
- production: 生产环境

**访问方式**:
```python
from services.config_manager import get_api_base_url, get_api_timeout

base_url = get_api_base_url()
timeout = get_api_timeout()
```

### 3. 日志系统
**决策**: 使用 loguru 而不是标准logging

**原因**:
- 更简洁的API
- 自动日志轮转
- 更好的格式化

**使用**:
```python
from utils import logger

logger.info("信息")
logger.success("成功")
logger.error("错误")
logger.debug("调试")
```

### 4. UI框架选择
**决策**: PySide6 + QFluentWidgets

**原因**:
- 跨平台支持
- 现代化UI设计
- 丰富的组件库
- 良好的性能

### 5. 打包方案
**决策**: PyInstaller（主要） + Nuitka（可选）

**PyInstaller**:
- 快速打包
- 支持多平台
- 配置灵活

**Nuitka**:
- 编译为C代码
- 性能更好
- 代码保护

## 数据流架构

### ASR处理流程
```
视频文件 → 音频提取 → ASR引擎 → 字幕生成 → NLP优化 → SRT文件
```

**涉及模块**:
1. `app/video_tools.py`: 视频处理
2. `app/cloud_asr/`: ASR服务
3. `app/nlp_api/`: NLP处理
4. `app/smart_sentence_processor.py`: 句子优化

### 翻译处理流程
```
SRT文件 → 术语提取 → 分块翻译 → LLM优化 → 翻译SRT
```

**涉及模块**:
1. `agent/translator.py`: 翻译器
2. `agent/terminology_manager.py`: 术语管理
3. `services/llm_client.py`: LLM客户端

### UI交互流程
```
用户操作 → UI事件 → 信号发射 → 任务队列 → 工作线程 → 结果回调 → UI更新
```

**涉及模块**:
1. `nice_ui/ui/`: UI界面
2. `nice_ui/task/`: 任务处理
3. `nice_ui/configure/signal.py`: 信号定义

## 安全架构

### 1. 凭证管理
**位置**: `.credentials/`

**加密**: 使用加密存储敏感信息
- `aliyun_credentials.enc`: 加密的阿里云凭证

**工具**: `utils/crypto_utils.py`

### 2. API密钥管理
**存储**: 本地QSettings
**访问**: 通过服务层封装
**原则**: 永不硬编码，永不提交到Git

### 3. 网络安全
**代理支持**: HTTP/SOCKS5代理
**超时设置**: 防止无限等待
**重试机制**: 配置化的重试策略

## 性能优化策略

### 1. 懒加载
**实现**: `utils/lazy_loader.py`
**用途**: 延迟加载大型模块

### 2. 资源管理
**实现**: `components/resource_manager.py`
**策略**: 
- 资源缓存
- 按需加载
- 及时释放

### 3. 数据库优化
**策略**:
- 使用索引
- 批量操作
- 连接池管理

### 4. UI优化
**策略**:
- 异步加载
- 虚拟滚动
- 防抖节流

## 扩展性设计

### 1. 插件化架构
**潜在扩展点**:
- 新的ASR引擎
- 新的翻译服务
- 新的LLM提供商

**实现方式**: 通过接口和工厂模式

### 2. 配置驱动
**可配置项**:
- API端点
- 模型参数
- UI主题
- 翻译策略

### 3. 国际化支持
**实现**: `nice_ui/language/`
- `zh.json`: 中文
- `en.json`: 英文

**扩展**: 添加新语言只需添加JSON文件

## 测试策略

### 1. 单元测试
**位置**: `test/`
**覆盖**: 核心业务逻辑

### 2. 集成测试
**测试**: API集成、数据库操作

### 3. UI测试
**方式**: 手动测试 + 自动化测试（待完善）

## 部署架构

### 1. 单机部署
**方式**: PyInstaller打包
**平台**: macOS, Windows

### 2. 依赖隔离
**方式**: 
- 打包所有依赖
- 复制必要的库文件
- 独立的Python环境

### 3. 更新机制
**实现**: `nice_ui/ui/version_check.py`
**流程**: 检查版本 → 提示更新 → 下载安装

## 最佳实践

### 1. 错误处理
- 使用try-except捕获异常
- 提供用户友好的错误提示
- 记录详细的错误日志

### 2. 资源清理
- 使用上下文管理器
- 及时关闭文件和连接
- 避免内存泄漏

### 3. 线程安全
- 使用Qt的线程安全机制
- 避免共享可变状态
- 使用信号槽通信

### 4. 代码复用
- 提取公共函数
- 使用继承和组合
- 避免重复代码
