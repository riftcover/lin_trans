# 代码库结构

## 目录组织

### 核心应用模块
```
app/
├── core/              # 核心功能
│   ├── config.py      # 配置管理
│   ├── security.py    # 安全相关
│   └── api_client.py  # API客户端（AuthenticationError, APIClient）
├── cloud_asr/         # 云端ASR服务
│   ├── aliyun_asr_client.py    # 阿里云ASR客户端
│   ├── aliyun_oss_client.py    # 阿里云OSS客户端
│   ├── gladia_asr_client.py    # Gladia ASR客户端
│   ├── gladia_task_manager.py  # Gladia任务管理
│   └── task_manager.py         # ASR任务管理器
├── cloud_trans/       # 云端翻译服务
│   └── task_manager.py
├── nlp_api/          # NLP API
│   └── nlp_client.py
├── spacy_utils/      # Spacy工具
├── video_tools.py    # 视频处理工具
├── smart_sentence_processor.py  # 智能句子处理
├── split_nlp.py      # NLP分割
└── listen.py         # 监听服务
```

### UI模块
```
nice_ui/
├── ui/               # UI界面
│   ├── MainWindow.py      # 主窗口（Window类）
│   ├── setting_ui.py      # 设置界面
│   ├── login.py           # 登录界面
│   ├── video2srt.py       # 视频转字幕
│   ├── work_srt.py        # 字幕工作区
│   ├── srt_edit.py        # 字幕编辑
│   ├── profile.py         # 用户资料
│   ├── purchase_dialog.py # 购买对话框
│   ├── check_page.py      # 检查页面
│   ├── version_check.py   # 版本检查
│   ├── my_story.py        # 我的故事
│   ├── SingalBridge.py    # 信号桥接
│   └── style.py           # 样式定义
├── configure/        # 配置
│   ├── config.py          # 配置类
│   ├── signal.py          # 信号定义
│   ├── setting_cache.py   # 设置缓存
│   └── custom_exceptions.py  # 自定义异常
├── managers/         # 管理器
│   └── ui_manager.py      # UI管理器
├── services/         # 服务层
│   ├── service_provider.py    # 服务提供者
│   ├── auth_service.py        # 认证服务
│   ├── api_service.py         # API服务
│   ├── simple_api_service.py  # 简单API服务
│   ├── token_service.py       # Token服务
│   └── token_refresh_service.py  # Token刷新服务
├── interfaces/       # 接口定义
│   ├── auth.py            # 认证接口
│   ├── token.py           # Token接口
│   └── ui_manager.py      # UI管理器接口
├── task/             # 任务处理
│   ├── main_worker.py     # 主工作线程（Worker, QueueConsumer）
│   ├── queue_worker.py    # 队列工作线程
│   ├── api_thread.py      # API线程
│   └── orm_factory.py     # ORM工厂
├── util/             # 工具函数
│   ├── tools.py
│   ├── file_check.py
│   ├── data_converter.py
│   ├── code_tools.py
│   └── get_size.py
└── language/         # 国际化
    ├── zh.json        # 中文
    └── en.json        # 英文
```

### 翻译代理模块
```
agent/
├── translator.py              # 翻译器（Translator类）
├── enhanced_common_agent.py   # 增强通用代理
├── srt_translator_adapter.py  # SRT翻译适配器
├── terminology_manager.py     # 术语管理器
└── model_down.py             # 模型下载
```

### 组件模块
```
components/
├── widget/           # 自定义组件
│   ├── subedit.py         # 字幕编辑器
│   ├── player.py          # 播放器
│   ├── combo_box.py       # 下拉框
│   ├── button.py          # 按钮
│   ├── pagination.py      # 分页
│   ├── status_labe.py     # 状态标签
│   ├── transaction_table.py  # 交易表格
│   ├── custom_splitter.py    # 自定义分割器
│   └── qfluent_change/       # QFluent修改
│       ├── line_edit.py
│       └── check_box.py
├── common/           # 通用组件
│   ├── icon.py
│   ├── color.py
│   └── size.py
├── themes/           # 主题样式（QSS文件）
├── assets/           # 资源文件（图标、图片）
├── lin_resource.qrc  # Qt资源文件
├── lin_resource_rc.py  # 编译后的资源
├── resource_manager.py  # 资源管理器
└── update_resources.py  # 更新资源
```

### 服务模块
```
services/
├── config_manager.py  # 配置管理器
├── llm_client.py      # LLM客户端（支持多种API）
└── decorators.py      # 装饰器
```

### 工具模块
```
utils/
├── config_manager.py  # 配置管理
├── log.py            # 日志工具
├── file_utils.py     # 文件工具
├── crypto_utils.py   # 加密工具
├── crypto_gui.py     # 加密GUI
├── agent_dict.py     # 代理字典
└── lazy_loader.py    # 懒加载
```

### 数据库模块
```
orm/
├── inint.py          # 初始化
├── queries.py        # 查询（PromptsOrm等）
└── linlin.db         # SQLite数据库文件
```

### 测试模块
```
test/
├── test_funasr_zn_sub.py      # FunASR中文测试
├── test_funasr_snese_sub.py   # FunASR句子测试
├── test_nlp_file.py           # NLP文件测试
├── test_sentence_len.py       # 句子长度测试
├── test_asr_cloud.py          # 云端ASR测试
└── ta_asr_result.json         # 测试结果
```

### 配置文件
```
config/
└── api_config.yaml   # API配置（开发/测试/生产环境）
```

### 示例代码
```
example/
├── use_feature_app.py         # 功能使用示例
├── concurrent_api_ui.py       # 并发API UI示例
├── concurrent_api_simple.py   # 简单并发API
├── concurrent_api_practical.py  # 实用并发API
├── concurrent_ui_with.py      # 并发UI
├── clent_use.py              # 客户端使用
├── clent_use_thread.py       # 客户端线程使用
├── history_use.py            # 历史使用
├── recharge_use.py           # 充值使用
└── translate_use.py          # 翻译使用
```

### 第三方库
```
vendor/
└── qfluentwidgets/   # QFluentWidgets UI库（完整源码）
```

### 其他重要目录
```
.credentials/         # 凭证文件（加密）
logs/                # 日志文件
tmp/                 # 临时文件
models/              # 模型文件（gitignore）
result/              # 输出结果（gitignore）
docs/                # 文档
website/             # 网站相关
creat/               # 创建工具
tools/               # 工具脚本
videotrans/          # 视频翻译（translator子模块）
```

## 入口文件
- **run.py**: 主入口（开发环境）
- **start.py**: 启动入口（生产环境）
- **install_build.py**: PyInstaller打包脚本
- **tbuild.py**: Nuitka编译脚本
- **build_setting_ui.py**: 设置UI构建

## 关键设计模式
1. **依赖注入**: ServiceProvider管理服务实例
2. **接口抽象**: interfaces目录定义接口契约
3. **任务队列**: 使用队列处理ASR和翻译任务
4. **信号槽机制**: Qt信号槽实现UI与业务逻辑解耦
5. **ORM模式**: SQLAlchemy管理数据库操作
