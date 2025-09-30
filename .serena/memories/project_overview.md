# 项目概览

## 项目名称
**lin-trans** (Lapped AI 字幕助手)

## 项目目的
一款为内容创作者而生的字幕助手，主要功能包括：
- 视频语音识别（ASR）转字幕
- 字幕翻译
- 字幕编辑
- 云端ASR服务集成
- LLM辅助翻译优化

## 核心价值
为视频内容创作者提供高效的字幕生成和翻译工具，支持本地和云端两种处理方式。

## 技术栈

### 前端UI框架
- **PySide6 (6.7.2)**: Qt for Python，主UI框架
- **qfluentwidgets**: Fluent Design风格的UI组件库（vendor目录）
- **darkdetect**: 系统主题检测

### 后端核心
- **Python 3.11**: 主要开发语言（要求 >=3.11, <3.13）
- **PyTorch 2.4.1**: 深度学习框架
- **FunASR 1.2.6**: 阿里达摩院语音识别引擎
- **ModelScope 1.25.0**: 模型管理

### ASR相关
- **funasr**: 本地语音识别
- **torchaudio 2.4.1**: 音频处理
- **av 14.4.0**: 视频处理
- **scipy 1.15.2**: 科学计算

### 云服务集成
- **阿里云OSS**: alibabacloud-oss-v2 1.1.0
- **阿里云DashScope**: dashscope 1.23.1
- **Gladia ASR**: 云端语音识别服务

### LLM集成
- **OpenAI SDK 1.76.0**: 支持多种LLM API（Kimi、智谱、通义千问、DeepSeek）
- **httpx 0.27.2**: HTTP客户端

### NLP处理
- **spacy 3.8.7**: 自然语言处理
- **spacy-pkuseg 0.0.33**: 中文分词

### 数据库
- **SQLAlchemy 2.0.40**: ORM框架
- **SQLite**: 本地数据库（orm/linlin.db）

### 配置管理
- **Pydantic 2.9.2**: 数据验证
- **pydantic_settings 2.9.1**: 配置管理
- **PyYAML**: YAML配置文件解析

### 打包部署
- **PyInstaller 6.11.0**: 应用打包
- **Nuitka 2.7.12**: Python编译器（可选）

### 工具库
- **loguru 0.7.3**: 日志管理
- **json-repair 0.50.1**: JSON修复
- **packaging 25.0**: 版本管理
- **pytz 2025.2**: 时区处理

## 项目版本
当前版本: **0.2.1**

## 支持平台
- macOS (主要开发平台，支持 Apple Silicon arm64 和 x86_64)
- Windows

## 许可证
根据LICENSE文件确定（项目根目录存在LICENSE文件）
