import os

from app.spacy_utils.load_nlp_model import init_nlp
from app.spacy_utils.sentence_processor import split_segments_by_boundaries
from utils.file_utils import funasr_write_srt_file
# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
segments = [{
    'text': '嗯，',
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

# segments = [{'text': 'Picture a winter wonderland,', 'timestamp': [
#             [
#                 0,
#                 478
#             ],
#             [
#                 478,
#                 717
#             ],
#             [
#                 717,
#                 1196
#             ],
#             [
#                 1196,
#                 1913
#             ]
#         ]
#     }]
srt_file_path = os.path.join(current_dir, 'ta_asr_result.srt')
nlp = init_nlp('zh')
segments_new = split_segments_by_boundaries(segments, nlp)
print(segments_new)

funasr_write_srt_file(segments_new, srt_file_path)




# print(segments_new)
