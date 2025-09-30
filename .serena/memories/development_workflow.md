# 开发工作流程

## 环境设置

### 1. 克隆项目
```bash
git clone git@github.com:riftcover/lin_trans.git
cd lin_trans
```

### 2. 创建虚拟环境
```bash
# 使用uv（推荐）
uv venv

# 激活虚拟环境
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. 安装依赖
```bash
# 使用uv
uv sync

# 或使用pip
pip install -r requirements.txt
```

### 4. 配置环境
```bash
# 设置开发环境
export APP_ENV=development

# 创建必要的目录
mkdir -p models result logs orm
```

## 开发流程

### 1. 创建功能分支
```bash
# 从main分支创建新分支
git checkout main
git pull origin main
git checkout -b feat/new-feature

# 或修复bug
git checkout -b fix/bug-description
```

### 2. 开发新功能

#### 步骤1: 设计
- 明确功能需求
- 设计数据结构
- 确定接口契约
- 考虑向后兼容性

#### 步骤2: 实现
- 遵循代码风格规范
- 添加类型提示
- 编写文档字符串
- 添加适当的日志

#### 步骤3: 测试
- 编写单元测试
- 手动功能测试
- 测试边界情况
- 跨平台测试（如适用）

### 3. 代码提交

#### 提交前检查
```bash
# 检查代码风格（建议）
black .
isort .

# 类型检查（建议）
mypy app/ nice_ui/ agent/

# 运行测试
python test/test_*.py
```

#### Git提交
```bash
# 查看修改
git status
git diff

# 添加文件
git add <files>

# 提交（使用清晰的提交信息）
git commit -m "feat: 添加新功能描述"
# 或
git commit -m "fix: 修复bug描述"
# 或
git commit -m "docs: 更新文档"
```

#### 提交信息规范
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 4. 推送和PR

```bash
# 推送到远程
git push origin feat/new-feature

# 在GitHub上创建Pull Request
# 填写PR描述，说明改动内容
```

## 调试技巧

### 1. 日志调试
```python
from utils import logger

# 添加调试日志
logger.debug(f"变量值: {variable}")
logger.info(f"执行到这里: {step}")
```

### 2. 断点调试
```python
# 使用pdb
import pdb; pdb.set_trace()

# 或使用IDE断点（推荐）
# VSCode, PyCharm等都支持图形化断点调试
```

### 3. UI调试
```python
# 打印窗口大小
def print_window_size(self):
    size = self.size()
    print(f"窗口大小: 宽度={size.width()}, 高度={size.height()}")

# 打印组件位置
pos = widget.mapToGlobal(widget.rect().topLeft())
print(f"组件位置: x={pos.x()}, y={pos.y()}")
```

### 4. 网络调试
```python
# 使用httpx的事件钩子
import httpx

def log_request(request):
    logger.debug(f"请求: {request.method} {request.url}")

def log_response(response):
    logger.debug(f"响应: {response.status_code}")

client = httpx.Client(
    event_hooks={'request': [log_request], 'response': [log_response]}
)
```

## 常见开发任务

### 1. 添加新的UI页面

#### 步骤
1. 在 `nice_ui/ui/` 创建新文件
2. 继承 `QWidget` 或其他Qt组件
3. 实现 `setup_ui()` 方法
4. 实现 `bind_action()` 方法
5. 在主窗口中添加页面

#### 示例
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout
from vendor.qfluentwidgets import BodyLabel

class NewPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setup_ui()
        self.bind_action()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(BodyLabel("新页面"))
        
    def bind_action(self):
        pass
```

### 2. 添加新的API端点

#### 步骤
1. 在 `app/core/api_client.py` 添加方法
2. 定义请求和响应模型（使用Pydantic）
3. 处理错误和异常
4. 添加日志记录

#### 示例
```python
def new_api_call(self, param: str) -> dict:
    """新的API调用"""
    try:
        response = self.client.post(
            f"{self.base_url}/new-endpoint",
            json={"param": param}
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"API调用失败: {e}")
        raise
```

### 3. 添加新的配置项

#### 步骤
1. 在 `config/api_config.yaml` 添加配置
2. 在 `services/config_manager.py` 添加访问函数
3. 更新文档

#### 示例
```yaml
# config/api_config.yaml
production:
  new_config: "value"
```

```python
# services/config_manager.py
def get_new_config() -> str:
    """获取新配置"""
    return config_manager.get_config("new_config")
```

### 4. 添加新的数据库表

#### 步骤
1. 在 `orm/` 定义ORM模型
2. 创建查询类
3. 更新数据库初始化脚本
4. 添加迁移逻辑（如需要）

#### 示例
```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class NewTable(Base):
    __tablename__ = 'new_table'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
```

### 5. 集成新的LLM提供商

#### 步骤
1. 在 `services/llm_client.py` 添加客户端创建逻辑
2. 在 `nice_ui/ui/setting_ui.py` 添加API Key输入
3. 更新配置管理
4. 测试集成

### 6. 添加新的ASR引擎

#### 步骤
1. 在 `app/cloud_asr/` 创建新的客户端
2. 实现统一的接口
3. 在任务管理器中注册
4. 添加UI配置选项

## 测试流程

### 1. 单元测试
```bash
# 运行特定测试
python test/test_funasr_zn_sub.py

# 使用pytest（如果配置）
pytest test/
```

### 2. 集成测试
```bash
# 测试API集成
python test/test_asr_cloud.py

# 测试NLP功能
python test/test_nlp_file.py
```

### 3. UI测试
```bash
# 启动应用进行手动测试
python run.py

# 测试不同场景
# - 创建新任务
# - 编辑字幕
# - 翻译功能
# - 设置页面
```

### 4. 打包测试
```bash
# 构建应用
python install_build.py

# 测试打包后的应用
cd dist/Lapped
./Lapped  # macOS
# 或
Lapped.exe  # Windows
```

## 性能优化

### 1. 性能分析
```bash
# 使用cProfile
python -m cProfile -o output.prof run.py

# 分析结果
python -m pstats output.prof
```

### 2. 内存分析
```python
# 使用memory_profiler
from memory_profiler import profile

@profile
def my_function():
    pass
```

### 3. UI性能
- 使用虚拟滚动处理大列表
- 延迟加载非关键组件
- 优化信号槽连接

## 文档维护

### 1. 代码文档
- 为所有公共API添加文档字符串
- 使用类型提示
- 添加使用示例

### 2. 项目文档
- 更新 `docs/` 目录下的文档
- 保持README.md最新
- 记录重要的设计决策

### 3. 示例代码
- 在 `example/` 目录添加示例
- 确保示例代码可运行
- 添加注释说明

## 发布流程

### 1. 版本准备
```bash
# 更新版本号
# 编辑 nice_ui/ui/__init__.py
__version__ = "0.2.2"

# 编辑 pyproject.toml
version = "0.2.2"
```

### 2. 更新变更日志
```markdown
# CHANGELOG.md

## [0.2.2] - 2025-XX-XX
### Added
- 新功能描述

### Fixed
- Bug修复描述

### Changed
- 变更描述
```

### 3. 构建发布包
```bash
# 清理旧构建
rm -rf build/ dist/

# 构建
python install_build.py

# 测试构建结果
cd dist/Lapped
./Lapped
```

### 4. 创建Git标签
```bash
# 提交所有变更
git add .
git commit -m "chore: 发布版本 0.2.2"

# 创建标签
git tag -a v0.2.2 -m "版本 0.2.2"

# 推送标签
git push origin v0.2.2
```

### 5. GitHub Release
1. 在GitHub上创建新Release
2. 选择标签 v0.2.2
3. 填写发布说明
4. 上传构建的应用包
5. 发布

## 故障排查

### 1. 依赖问题
```bash
# 重新安装依赖
uv sync --reinstall

# 清理缓存
uv cache clean
```

### 2. 数据库问题
```bash
# 备份数据库
cp orm/linlin.db orm/linlin.db.backup

# 重建数据库
rm orm/linlin.db
# 重新运行应用初始化数据库
```

### 3. 打包问题
```bash
# 清理构建文件
rm -rf build/ dist/ *.spec

# 使用调试模式
python install_build.py --debug
```

### 4. UI问题
- 检查Qt版本兼容性
- 清理QSettings缓存
- 重置UI配置

## 协作开发

### 1. 代码审查
- 审查PR时关注代码质量
- 检查是否遵循项目规范
- 测试功能是否正常
- 提供建设性反馈

### 2. 问题跟踪
- 使用GitHub Issues跟踪bug
- 使用标签分类问题
- 及时响应和更新

### 3. 沟通
- 重大变更前讨论
- 记录设计决策
- 分享知识和经验

## 持续改进

### 1. 技术债务
- 定期审查代码
- 重构复杂代码
- 更新过时依赖

### 2. 性能优化
- 监控性能指标
- 优化瓶颈
- 减少资源消耗

### 3. 用户体验
- 收集用户反馈
- 改进UI/UX
- 简化操作流程
