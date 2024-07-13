from PySide6.QtCore import QSettings
from openai import OpenAI

settings = QSettings("Locoweed", "LinLInTrans")
qwen_key = settings.value("qwen", type=str)
print(type(qwen_key))
def get_response():
    client = OpenAI(api_key = qwen_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 填写DashScope服务的base_url
                    )
    completion = client.chat.completions.create(model="qwen-plus", messages=[
        {'role': 'system',
         'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': '你是谁？'}
    ])
    print(completion.model_dump_json())


if __name__ == '__main__':
    get_response()
