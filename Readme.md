## 变更tmp下资源文件
1. lin_resource.qrc中添加相关路径
2. pyside6-rcc lin_resource.qrc -o lin_resource_rc.py生成二进制文件
3. resource_manager.py中_load_all_styles添加对应映射


ps -ef | grep linlin | awk '{print $2}' | xargs kill -9


ffmpeg目录(plugin)为项目同级目录
models目录为项目同级目录

# funasr 变更
from funasr.utils.postprocess_utils import rich_transcription_postprocess
```angular2html
def rich_transcription_postprocess(s):
    def get_emo(s):
        return s[-1] if s[-1] in emo_set else None

    def get_event(s):
        return s[0] if s[0] in event_set else None


    s = s.replace("<|nospeech|><|Event_UNK|>", "❓")

    for lang in lang_dict:
        s = s.replace(lang, "<|lang|>")
    s_list = [format_str_v2(s_i).strip(" ") for s_i in s.split("<|lang|>")]
    new_s = " " + s_list[0]
    cur_ent_event = get_event(new_s)
    for i in range(1, len(s_list)):
        if len(s_list[i]) == 0:
            continue
        if get_event(s_list[i]) == cur_ent_event and get_event(s_list[i]) != None:
            s_list[i] = s_list[i][1:]
        # else:
        cur_ent_event = get_event(s_list[i])
        if get_emo(s_list[i]) != None and get_emo(s_list[i]) == get_emo(new_s):
            new_s = new_s[:-1]
        new_s += s_list[i].strip().lstrip()
    new_s = new_s.replace("The.", " ")
    for emoji in emo_set.union(event_set):
        new_s = new_s.replace(emoji, " ")
    return new_s.strip()
```

for emoji in emo_set.union(event_set):
    new_s = new_s.replace(emoji, " ")
是新添加的,为了取消输出文本中的emoji


## 打包注意事项
1.tmp/asr_tasks.json 是asr云任务持久化文件，需要在打包时包含进去一个空列表[]