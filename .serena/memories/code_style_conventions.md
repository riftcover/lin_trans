# 代码风格与约定

## Python版本
- **要求**: Python >= 3.11, < 3.13
- **当前开发环境**: Python 3.11.4

## 命名约定

### 类名
- **风格**: PascalCase（大驼峰）
- **示例**: 
  - `APIClient`
  - `ASRTaskManager`
  - `AuthService`
  - `MainWindow`

### 函数/方法名
- **风格**: snake_case（蛇形命名）
- **示例**:
  - `get_api_base_url()`
  - `check_login_status()`
  - `download_model()`
  - `apply_proxy()`

### 变量名
- **风格**: snake_case
- **示例**:
  - `model_path`
  - `api_base_url`
  - `current_version`

### 常量
- **风格**: UPPER_SNAKE_CASE（全大写蛇形）
- **示例**:
  - `UNIFORM_SPACING`
  - `PROJECT_ROOT`
  - `MODELS_DIR`

### 私有成员
- **前缀**: 单下划线 `_`
- **示例**:
  - `_init_table()`
  - `_setup_api_worker()`
  - `_on_data_received()`

## 类型提示
- **使用**: 项目中广泛使用类型提示
- **示例**:
```python
from typing import Optional

def save_prompt(self, key_id: Optional[int], prompt_name: str, prompt_msg: str) -> bool:
    pass

def handle_response(self, reply: QNetworkReply) -> None:
    pass
```

## 文档字符串
- **风格**: 简洁的单行或多行文档字符串
- **示例**:
```python
def clean_logs_directory():
    """清空 logs 文件夹中的所有文件，但保留文件夹"""
    pass

def custom_ignore(src, names):
    """
    检查是否在排除目录列表中
    排除目录和文件
    """
    pass
```

## 导入顺序
1. **标准库**: os, sys, subprocess等
2. **第三方库**: PySide6, torch, httpx等
3. **本地模块**: 项目内部模块

**示例**:
```python
import os
import sys
import multiprocessing

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QUrl

from nice_ui.ui.MainWindow import Window
from utils import logger
```

## 代码组织

### 类结构顺序
1. 类变量
2. `__init__` 方法
3. 公共方法
4. 私有方法（`_`前缀）
5. 槽函数（`@Slot`装饰器）

### 布局规范
```python
class ExampleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setup_ui()      # UI初始化
        self.bind_action()   # 绑定事件
        
    def setup_ui(self):
        """设置UI"""
        pass
        
    def bind_action(self):
        """绑定动作"""
        pass
```

## Qt特定约定

### 信号槽连接
```python
# 使用 @Slot 装饰器
@Slot(str, dict)
def _on_data_received(self, endpoint_name: str, result: dict):
    pass

# 连接信号
self.button.clicked.connect(self.on_button_clicked)
```

### 资源管理
- Qt资源文件: `lin_resource.qrc`
- 编译命令: `pyside6-rcc components/lin_resource.qrc -o components/lin_resource_rc.py`
- 资源映射: 在 `resource_manager.py` 中的 `_load_all_styles` 添加映射

## 日志规范
- **使用**: loguru库
- **级别**: debug, info, success, warning, error
- **示例**:
```python
from utils import logger

logger.info(f"模型存储路径: {config.models_path}")
logger.success(f"模型安装成功: {model_folder}")
logger.error(f"模型安装失败: {model_folder}")
logger.debug(f"编辑prompt,所在行:{button_row}")
```

## 异常处理
```python
try:
    # 操作
    pass
except Exception as e:
    logger.error(f"操作失败: {str(e)}")
    InfoBar.error(
        title="错误",
        content=f"操作失败: {str(e)}",
        parent=self,
    )
```

## 配置管理
- **配置文件**: YAML格式（`config/api_config.yaml`）
- **环境**: development, test, production
- **访问**: 通过 `services/config_manager.py` 的函数

## 多进程注意事项
```python
# macOS + PyInstaller 必须设置
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

# 冻结支持
multiprocessing.freeze_support()
```

## UI间距规范
- **统一间距**: 定义常量如 `UNIFORM_SPACING = 10`
- **卡片边距**: `setContentsMargins(20, 20, 20, 20)`
- **布局间距**: `setSpacing(15)`

## 注释规范
- **TODO注释**: 标记待完成的工作
- **中文注释**: 项目中使用中文注释
- **行内注释**: 解释复杂逻辑

## 代码质量
- **无Linter配置**: 项目中未找到 .flake8, .pylintrc, pytest.ini
- **建议**: 保持代码简洁，遵循现有风格
- **复杂度**: 避免过深的嵌套（参考Linus哲学：超过3层缩进需要重构）
