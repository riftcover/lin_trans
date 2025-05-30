from app.spacy_utils.load_nlp_model import init_nlp
from app.spacy_utils.sentence_processor import get_sub_index, set_nlp

segments = [{
    'text': '嗯，',
    'start': 2290,
    'end': 2530,
    'timestamp': [
        [
            2290,
            2530
        ]
    ],
    'spk': 0
},
    {
        'text': '呃欢迎大家来继续参加我的精益产品探索的课程。',
        'start': 8600,
        'end': 12060,
        'timestamp': [
            [
                8600,
                8820
            ],
            [
                8820,
                8940
            ],
            [
                8940,
                9060
            ],
            [
                9060,
                9180
            ],
            [
                9180,
                9360
            ],
            [
                9360,
                9500
            ],
            [
                9500,
                9660
            ],
            [
                9660,
                9900
            ],
            [
                9920,
                10080
            ],
            [
                10080,
                10280
            ],
            [
                10280,
                10440
            ],
            [
                10440,
                10680
            ],
            [
                10680,
                10800
            ],
            [
                10800,
                11000
            ],
            [
                11000,
                11100
            ],
            [
                11100,
                11300
            ],
            [
                11300,
                11400
            ],
            [
                11400,
                11580
            ],
            [
                11580,
                11700
            ],
            [
                11700,
                11820
            ],
            [
                11820,
                12060
            ]
        ],
        'spk': 0
    }, ]
segments_new = []
nlp = init_nlp('zh')
for segment in segments:
    split_text_list, split_index = set_nlp(segment['text'], nlp)
    if len(split_text_list) <= 1:
        segments_new.append(segment)
    else:
        split_len = len(split_text_list)
        timestamp = segment.get('timestamp')
        start = 0
        for i in range(split_len):
            segment_dict = {}
            ll = len(split_text_list[i])
            end = start + ll - 1
            print(end)
            if i < split_len - 1:
                segment_dict = {
                    'text': split_text_list[i],
                    'start': timestamp[start][0],
                    'end': timestamp[end][1]
                }

            else:
                segment_dict = {
                    'text': split_text_list[i],
                    'start': timestamp[start + 1][0],
                    'end': timestamp[-1][1]
                }
            start = end

            segments_new.append(segment_dict)



print(segments_new)
