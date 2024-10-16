## 变更tmp下资源文件
1. lin_resource.qrc中添加相关路径
2. pyside6-rcc lin_resource.qrc -o lin_resource_rc.py生成二进制文件
3. resource_manager.py中_load_all_styles添加对应映射


ps -ef | grep linlin | awk '{print $2}' | xargs kill -9


ffmpeg目录(plugin)为项目同级目录
models目录为项目同级目录