# 凭证管理指南

本文档说明如何安全地管理阿里云等敏感凭证信息。

## 背景

为了提高安全性，我们不再在代码中直接存储敏感凭证信息，而是使用加密的方式存储这些信息。

## 设置凭证的方法

有两种方式可以设置凭证：

### 1. 使用加密的凭证文件（推荐）

我们提供了一个工具脚本，用于生成加密的凭证文件：

```bash
# 方法1：交互式输入
python tools/generate_credentials.py

# 方法2：命令行参数
python tools/generate_credentials.py --aki YOUR_AKI --aks YOUR_AKS --asr_api_key YOUR_ASR_API_KEY
```

这将在项目根目录下的 `.credentials` 文件夹中创建一个加密的凭证文件。程序会自动从这个文件中读取凭证信息。

### 2. 使用环境变量

如果您不想使用加密文件，也可以通过设置环境变量来提供凭证信息：

```bash
# Windows
set ALIYUN_AKI=YOUR_AKI
set ALIYUN_AKS=YOUR_AKS
set ALIYUN_REGION=cn-beijing
set ALIYUN_BUCKET=asr-file-tth
set ALIYUN_ASR_API_KEY=YOUR_ASR_API_KEY
set ALIYUN_ASR_MODEL=paraformer-v2

# Linux/macOS
export ALIYUN_AKI=YOUR_AKI
export ALIYUN_AKS=YOUR_AKS
export ALIYUN_REGION=cn-beijing
export ALIYUN_BUCKET=asr-file-tth
export ALIYUN_ASR_API_KEY=YOUR_ASR_API_KEY
export ALIYUN_ASR_MODEL=paraformer-v2
```

## 加密密钥

默认情况下，程序使用一个内置的默认密钥进行加密。如果您想使用自定义密钥，可以设置环境变量 `LINLIN_CRYPTO_KEY`：

```bash
# Windows
set LINLIN_CRYPTO_KEY=your_custom_key

# Linux/macOS
export LINLIN_CRYPTO_KEY=your_custom_key
```

或者在生成凭证时指定密码：

```bash
python tools/generate_credentials.py --password your_custom_key
```

## 安全建议

1. 不要将凭证文件提交到版本控制系统中
2. 不要在公共场合或不安全的地方输入或显示凭证信息
3. 定期更换凭证
4. 使用最小权限原则，只授予必要的权限

## 故障排除

如果您遇到凭证相关的问题，请检查：

1. 凭证文件是否存在
2. 环境变量是否正确设置
3. 加密密钥是否正确

如果问题仍然存在，可以尝试重新生成凭证文件。
