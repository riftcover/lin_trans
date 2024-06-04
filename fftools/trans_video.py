import moviepy.editor as mp





# video_path_parents = "/Users/locodol/Movies/ski/别人的教学视频/big picture"
# video_path_full = f'{video_path_parents}/mogul'
video_name ='tt1'
# video = mp.VideoFileClip(f'{video_path_full}/{video_name}')
video = mp.VideoFileClip('../data/tt1.mp4')
audio_path = f"{video_name}.wav"
video.audio.write_audiofile(audio_path)

