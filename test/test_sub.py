
b= [{'key': 'rand_key_1t9EwL56nGisi',
     'text': " When you go out there, i really encourage you to try and sense your body more and sense the skis on the snow, because that enables you to then switch off the overcrical part of your brain and really start skiing by feel. And that's what the best skiers are doing.",
     'punc_array': [1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1,
        1, 1, 3]}]

words = b[0].get('text').split()
for i,word in enumerate(words):
    print(i, word)
punc_list = b[0].get('punc_array')
for i,j in enumerate(punc_list):
    if j !=1:
        print(i)