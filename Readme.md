## 变更pyside静态资源文件
1. lin_resource.qrc中添加相关路径
2. 生成二进制文件
```bash
pyside6-rcc components/lin_resource.qrc -o components/lin_resource_rc.py
```
3. resource_manager.py中_load_all_styles添加对应映射

## 杀掉进程
```bash
ps -ef | grep lapped | awk '{print $2}' | xargs kill -9
```

## 打包注意事项
### 目录结构
ffmpeg目录(plugin)为项目同级目录
models目录为项目同级目录

## 依赖下载安装

```
### 1.下载离线安装包

```json lines
 pip download --prefer-binary --dest wheels -r requirements.txt     
```


### 2. 离线环境部署
```bash
pip install --no-index --find-links wheels -r requirements.txt
```




asr任务`funasr_zn_model`调整nlp功能由本地调整为线上：
1. 创建一个数据格式用来存储segments,生成的文件segment_data上传oss供线上nlp使用
2. 线上nlp功能与本地基本一致,唯一区别本地nlp功能在asr任务过程中执行,使用数据`segments`,线上nlp功能使用数据`segment_data`