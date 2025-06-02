## 变更pyside静态资源文件
1. lin_resource.qrc中添加相关路径
2. 生成二进制文件
```bash
pyside6-rcc components/lin_resource.qrc -o components/lin_resource_rc.py
```
3. resource_manager.py中_load_all_styles添加对应映射

## 杀掉进程
```bash
ps -ef | grep linlin | awk '{print $2}' | xargs kill -9
```

## 打包注意事项
### 目录结构
ffmpeg目录(plugin)为项目同级目录
models目录为项目同级目录