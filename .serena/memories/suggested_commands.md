# 常用命令

## 包管理

### UV包管理器（推荐）
项目使用 **uv** 作为包管理器（版本: 0.6.0）

```bash
# 安装依赖
uv pip install -r requirements.txt

# 同步依赖（根据 pyproject.toml）
uv sync

# 添加新依赖
uv add <package-name>

# 移除依赖
uv remove <package-name>
```

### 传统pip方式
```bash
# 安装依赖
pip install -r requirements.txt

# 下载离线安装包
pip download --prefer-binary --dest wheels -r requirements.txt

# 离线环境部署
pip install --no-index --find-links wheels -r requirements.txt
```

## 运行应用

### 开发环境
```bash
# 使用虚拟环境解释器
python run.py

# 或使用启动脚本
python start.py
```

### 生产环境
```bash
# 启动应用
python start.py
```

## Qt资源管理

### 更新资源文件
```bash
# 1. 在 lin_resource.qrc 中添加相关路径
# 2. 生成二进制文件
pyside6-rcc components/lin_resource.qrc -o components/lin_resource_rc.py

# 3. 在 resource_manager.py 的 _load_all_styles 中添加对应映射
```

## 打包构建

### PyInstaller打包
```bash
# 执行打包脚本
python install_build.py

# 调试模式打包
python install_build.py --debug
```

### Nuitka编译（可选）
```bash
# 编译模块
python tbuild.py
```

## 进程管理

### 杀掉应用进程（macOS）
```bash
# 查找并杀掉lapped进程
ps -ef | grep lapped | awk '{print $2}' | xargs kill -9
```

### 查看进程
```bash
# macOS/Linux
ps -ef | grep lapped

# 或使用
ps aux | grep python
```

## 测试

### 运行测试
```bash
# 运行特定测试文件
python test/test_funasr_zn_sub.py
python test/test_nlp_file.py
python test/test_asr_cloud.py
```

## 数据库

### SQLite数据库
```bash
# 数据库位置
orm/linlin.db

# 使用SQLite命令行工具
sqlite3 orm/linlin.db

# 查看表
.tables

# 退出
.quit
```

## 日志管理

### 查看日志
```bash
# 日志目录
logs/

# 实时查看日志（macOS/Linux）
tail -f logs/<log_file>

# 清空日志（由install_build.py自动执行）
```

## 模型管理

### 模型目录
```bash
# 默认模型路径
models/

# 打开模型目录（macOS）
open models/

# 打开模型目录（Windows）
explorer models
```

## 开发工具

### 代码格式化（建议）
```bash
# 使用black格式化
black .

# 使用isort排序导入
isort .
```

### 类型检查（建议）
```bash
# 使用mypy进行类型检查
mypy app/ nice_ui/ agent/
```

## Git操作

### 常用Git命令
```bash
# 查看状态
git status

# 提交更改
git add .
git commit -m "描述"

# 推送到远程
git push origin <branch-name>

# 拉取最新代码
git pull origin main
```

## macOS特定命令

### 文件操作
```bash
# 打开目录
open <directory>

# 查找文件
find . -name "*.py"

# 搜索内容
grep -r "search_term" .
```

### 系统信息
```bash
# 查看Python版本
python --version

# 查看系统架构
uname -m

# 查看macOS版本
sw_vers
```

## 环境变量

### 设置环境
```bash
# 设置应用环境（development/test/production）
export APP_ENV=development

# 查看环境变量
echo $APP_ENV
```

## 清理操作

### 清理构建文件
```bash
# 删除构建目录
rm -rf build/ dist/

# 删除Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 清理日志
rm -rf logs/*
```

## 依赖更新

### 更新依赖
```bash
# 使用uv更新所有依赖
uv pip install --upgrade -r requirements.txt

# 更新特定包
uv pip install --upgrade <package-name>
```

## 配置管理

### 编辑配置
```bash
# API配置
vim config/api_config.yaml

# 项目配置
vim pyproject.toml
```

## 加密凭证

### 管理凭证
```bash
# 凭证目录
.credentials/

# 加密的阿里云凭证
.credentials/aliyun_credentials.enc
```

## 性能分析（可选）

### 性能分析
```bash
# 使用cProfile
python -m cProfile -o output.prof run.py

# 分析结果
python -m pstats output.prof
```

## 注意事项
1. **虚拟环境**: 始终在虚拟环境中运行命令
2. **macOS特性**: 某些命令在macOS上有特殊要求（如multiprocessing）
3. **权限**: 某些操作可能需要管理员权限
4. **路径**: 所有相对路径都是相对于项目根目录
