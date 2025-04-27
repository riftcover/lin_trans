# 使用加密的嵌入式凭证替代明文阿里云敏感信息

## 背景

之前的代码中，阿里云的敏感信息（如AccessKey ID和Secret）是以明文形式存储在代码中的，这存在安全风险。

## 更改内容

1. 创建了加密工具类 `nice_ui/util/crypto_utils.py`，用于加密和解密敏感信息
2. 修改了 `nice_ui/configure/config.py` 中的 `aa_bb` 配置，使其从加密文件或环境变量中加载
3. 创建了工具脚本 `tools/generate_credentials.py`，用于生成加密的凭证文件
4. 添加了文档 `docs/credentials_usage.md`，说明如何使用加密凭证

## 实现方式

- 使用 Fernet 对称加密算法加密敏感信息
- 支持从环境变量或加密文件中加载凭证
- 提供了工具脚本，方便用户生成加密的凭证文件

## 使用方法

用户可以通过两种方式提供凭证信息：

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

## 测试

- 已测试从加密文件加载凭证
- 已测试从环境变量加载凭证
- 已测试在没有凭证的情况下使用空配置

## 安全性提升

- 敏感信息不再以明文形式存储在代码中
- 加密密钥可以通过环境变量自定义
- 遵循了最小权限原则
