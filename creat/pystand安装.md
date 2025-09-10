## pystand
1. 拷贝所有依赖
2. 运行程序,跑funasr任务
3. 运行ss.py 来瘦身依赖
4. 恢复以下内容:
4. 恢复nice_ui
5. lapped.int
5. D:\tool\pystand-py311-x64-true_new\runtime\Lib\site-packages\funasr\
6. modelscope



## pystand 如果需要pip安装依赖
1. creat\get-pip.py 拷贝到runtime目录中
2. python311._pth文件import site注释取消
3. 运行get-pip.py
```
python.exe get-pip.py
```
4. 按照whl文件
```
pip install --no-index --find-links wheels -r requirements.txt
```