"""
PyInstaller hook for FunASR library
自动发现并导入所有 FunASR 模型类，确保注册机制正常工作
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 收集所有 funasr 子模块
hiddenimports = collect_submodules('funasr')

# 特别确保关键模型模块被包含
critical_modules = [
    # 'funasr.models.paraformer.bi_cif_paraformer',
    # 'funasr.models.paraformer.paraformer',
    # 'funasr.models.sense_voice.model',
    # 'funasr.models.fsmn_vad.model',
    # 'funasr.models.ct_transformer.model',
    # 'funasr.models.campplus.model',
    # 'funasr.register',
    # 'funasr.auto.auto_model',
    # 'funasr.utils.postprocess_utils',
]

# 添加关键模块到隐式导入列表
for module in critical_modules:
    if module not in hiddenimports:
        hiddenimports.append(module)

# 收集数据文件（如果有配置文件等）
datas = collect_data_files('funasr', include_py_files=False)

print(f"FunASR Hook: 发现 {len(hiddenimports)} 个模块")
