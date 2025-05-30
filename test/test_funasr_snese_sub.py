from app.spacy_utils.load_nlp_model import init_nlp
from app.spacy_utils.sentence_processor import get_sub_index
from utils.file_utils import Segment, split_sentence

punctuation_res = [{'key': 'rand_key_1t9EwL56nGisi',
                    'text': " When you go out there, i really encourage you to try and sense your body more and sense the skis on the snow, because that enables you to then switch off the overcrical part of your brain and really start skiing by feel. And that's what the best skiers are doing.",
                    'punc_array': [1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1,
                                   1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1,
                                   1, 1, 3]}]
time_res = [{'key': 'rand_key_2yW4Acq9GFz6Y',
             'text': "when you go out there i really encourage you to try and sense your body more and sense the skis on the snow because that enables you to then switch off the OVERCRICAL part of your brain and really start skiing by feel and that's what the best skiers are doing",
             'timestamp': [[250, 370], [370, 530], [530, 710], [710, 950], [990, 1230], [1230, 1390], [1390, 1630], [1670, 2390], [2390, 2610], [2610, 2790],
                           [2790, 3030], [3290, 3390], [3390, 3870], [3870, 4010], [4010, 4250], [4370, 4610], [4610, 4850], [4950, 5290], [5290, 5430],
                           [5430, 5690], [5690, 5930], [6050, 6270], [6270, 6770], [7250, 7490], [7650, 7730], [7730, 8130], [8130, 8210], [8210, 8370],
                           [8370, 8530], [8530, 9270], [9270, 9470], [9470, 9570], [9570, 11390], [11390, 11510], [11510, 11610], [11610, 11750],
                           [11750, 12070], [12070, 12210], [12210, 12330], [12330, 12670], [12670, 13250], [13250, 13450], [13450, 13590], [13590, 13810],
                           [13810, 13970], [13970, 14070], [14070, 14150], [14150, 14390], [14410, 15150], [15550, 15750], [15750, 16425]]}]

# 长度不一致case
# punctuation_res= [{'key': 'rand_key_6J6afU1zT0YQO', 'text': ' Body alignment in your journey of skiing becomes more and more important as you start taking on steeper slopes. And building more forces during a skiton.',
#      'punc_array': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1,
#         1, 3]}]
# time_res =[{'key': 'rand_key_NO6n9JEC3HqdZ', 'text': 'body alignment in your journey of skiing becomes more and more important as you start taking on steeper slopes and building more forces during ASKITON', 'timestamp': [[2390, 2630], [2630, 3270], [3370, 3570], [3570, 3710], [3710, 4150], [4150, 4250], [4250, 4650], [4650, 5190], [5290, 5530], [5590, 5790], [5790, 5990], [5990, 6450], [6470, 6710], [6970, 7130], [7130, 7390], [7390, 7750], [7750, 7950], [7950, 8910], [8910, 9390], [9390, 9590], [9590, 9890], [9890, 10070], [10070, 10510], [10570, 11090], [11090, 12225]]}]

words = split_sentence(punctuation_res[0].get('text'))
# print(words)
# punc_list = punctuation_res[0].get('punc_array')
time_list = time_res[0].get('timestamp')

# print(len(words))
# print(len(punc_list))
# print(len(time_list))
# for i,word in enumerate(words):
#     print(i, word)
#
# for i,j in enumerate(punc_list):
#     if j !=1:
#         print(i)

msg = Segment(punctuation_res, time_res)
# punc_list = msg.get_segmented_index()
# print(punc_list)
# if not msg.ask_res_len():
#     msg.fix_wrong_index()
# nlp = init_nlp()
#
# split_list = get_sub_index(punc_list,words, nlp)
# print(split_list)
split_list = [4, 10, 15, 22, 36, 42, 50]
# # split_list = [4, 22, 42, 50]
start_time =1
rrl = msg.create_segmented_transcript(start_time, split_list)
print(rrl)
