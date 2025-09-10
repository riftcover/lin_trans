# 配置系统

本项目使用基于YAML的配置系统，用于管理不同环境下的应用程序设置。

## 配置文件

主要配置文件位于`config`目录下：

- `api_config.yaml`: API相关配置，包括基础URL、超时设置等

## 环境

配置系统支持多环境配置，默认包含以下环境：

- `development`: 开发环境
- `testing`: 测试环境
- `production`: 生产环境

默认使用的环境在配置文件的`default`字段中指定。

## 使用方法

### 在代码中使用配置

```python
# 导入配置管理器
from services.config_manager import get_api_base_url, get_api_timeout

# 获取API基础URL
base_url = get_api_base_url()

# 获取API超时时间
timeout = get_api_timeout()
```

## 配置文件格式

`api_config.yaml`文件的格式如下：

```yaml
# 开发环境
development:
  api_base_url: "http://127.0.0.1:8000/api"
  timeout: 15.0
  retry_attempts: 3
  retry_backoff: 0.5

# 测试环境
testing:
  api_base_url: "http://test-api.example.com/api"
  timeout: 10.0
  retry_attempts: 2
  retry_backoff: 0.3

# 生产环境
production:
  api_base_url: "http://123.57.206.182:8000/api"
  timeout: 30.0
  retry_attempts: 3
  retry_backoff: 1.0

# 默认环境
default: development
```

## 环境变量

配置系统也支持通过环境变量来指定当前环境：

```bash
# 设置环境变量
export APP_ENV=development
```

```
# 运行应用程序
python run.py
```

如果设置了`APP_ENV`环境变量，配置系统将优先使用该环境变量指定的环境。
