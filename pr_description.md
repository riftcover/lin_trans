# 代币消费系统与阿里云凭证安全加密

## 功能概述

本PR实现了两个主要功能：
1. 代币消费系统：用于跟踪和管理用户的代币消费
2. 阿里云凭证安全加密：将原本明文存储的阿里云敏感信息改为使用加密方式存储

## 代币消费系统

### 实现内容
- 添加了代币消费接口，支持不同功能的代币消费
- 完善了ASR云任务系统，支持任务完成后更新个人中心
- 实现了ASR云消费后更新个人主页的功能
- 添加了代币消费量管理器，负责存储和获取任务的代币消费量

### 核心文件
- `api_client.py`: 添加了消费代币接口
- `app/cloud_asr/task_manager.py`: 完善ASR云任务，支持代币消费
- `nice_ui/services/token_service.py`: 实现代币服务
- `nice_ui/ui/profile.py`: 更新个人主页显示代币信息

## 阿里云凭证安全加密

### 实现内容
- 创建了加密工具类，用于加密和解密敏感信息
- 修改了配置文件，使其从加密文件或环境变量中加载阿里云凭证
- 提供了工具脚本，方便用户生成加密的凭证文件
- 添加了详细的使用文档

### 核心文件
- `nice_ui/util/crypto_utils.py`: 加密工具类
- `nice_ui/configure/config.py`: 修改配置加载方式
- `tools/generate_credentials.py`: 生成加密凭证的工具脚本
- `docs/credentials_usage.md`: 使用说明文档

## 安全性提升
- 敏感信息不再以明文形式存储在代码中
- 加密密钥可以通过环境变量自定义
- 遵循了最小权限原则
- 支持从环境变量或加密文件中加载凭证

## 使用方法

### 代币消费系统
代币消费系统已集成到应用程序中，用户无需额外配置即可使用。系统会自动跟踪和管理用户的代币消费。

### 阿里云凭证
用户可以通过两种方式提供阿里云凭证：

1. 使用加密的凭证文件（推荐）：
   ```bash
   python tools/generate_credentials.py
   ```

2. 使用环境变量：
   ```bash
   # Windows
   set ALIYUN_AKI=YOUR_AKI
   set ALIYUN_AKS=YOUR_AKS
   
   # Linux/macOS
   export ALIYUN_AKI=YOUR_AKI
   export ALIYUN_AKS=YOUR_AKS
   ```

详细说明请参考 `docs/credentials_usage.md`。

## 测试情况
- 已测试代币消费接口
- 已测试ASR云任务系统
- 已测试从加密文件加载凭证
- 已测试从环境变量加载凭证
- 已测试在没有凭证的情况下使用空配置
