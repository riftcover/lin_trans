from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
# paraformer-zh is a multi-functional asr model
# use vad, punc, spk or not as you need
# model_name = 'speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch'
# model_name = 'speech_paraformer-large-vad-punc_asr_nat-en-16k-common-vocab10020'
model_name = 'SenseVoiceSmall'
model_dir = f'D:\\dcode\\models\\funasr\\iic\\{model_name}'
vad_model_dir = f'D:\\dcode\\models\\funasr\\iic/speech_fsmn_vad_zh-cn-16k-common-pytorch'
# input_file = r'D:\dcode\models\funasr\iic\speech_paraformer-large-vad-punc_asr_nat-en-16k-common-vocab10020\example\asr_example.wav'
input_file = r'D:\dcode\d0e24a75acddc02ced0cdb39c9f05b78\tt1.wav'

model = AutoModel(model=model_dir, model_revision="v2.0.4",
                  vad_model=vad_model_dir, vad_model_revision="v2.0.4",
                  punc_model="ct-punc-c", punc_model_revision="v2.0.4",
                  fa_model="fa-zh",fa_model_revision="v2.0.4",
                  # spk_model="cam++", spk_model_revision="v2.0.2",
                  vad_kwargs={"max_single_segment_time": 30000},
                  disable_update=True
                  )


res = model.generate(input=input_file,
                     batch_size_s=300,
                     use_fa=True,  # 启用强制对齐
                     output_word_timestamp=True  # 输出词级时间戳
                    #  use_punc=True
)
print(res)
# print(res[0]['sentence_info'])
# print(res[0]['text'])
# res =[{'key': 'tt1', 'text': " <|en|><|happy|><|speech|><|woitn|>today's podcast is about modifying ski bootss, and you're going to hear from my guest lou rosenfeld, who owned a successful ski shop in calgary for many years."}]
# print('-----------')
# text = rich_transcription_postprocess(res[0]['text'])
# print(text)

# text_with_punc = model.generate_punc(text)
# print(text_with_punc)
