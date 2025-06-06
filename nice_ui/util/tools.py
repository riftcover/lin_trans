# -*- coding: utf-8 -*-
import contextlib
import copy
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path
from typing import TypedDict, Union, Optional

from pydantic import BaseModel, Field

from nice_ui.configure import config
from nice_ui.configure.custom_exceptions import VideoProcessingError
from nice_ui.task import WORK_TYPE
from utils import logger


class ModelInfo(TypedDict):
    status: int
    model_name: str


class StartTools:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StartTools, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def match_source_model(source_model) -> ModelInfo:
        # 匹配源模型
        return config.model_list[source_model]

    @staticmethod
    def match_model_name(model_cn_name: str) -> str:
        model_info = config.model_list.get(model_cn_name, {})
        return model_info.get("model_name", "")

    @staticmethod
    def ask_model_folder(model_name: str) -> bool:
        # todo：当前是写死funasr，后续需要改成根据模型名称来获取模型路径
        is_installed = os.path.exists(
            os.path.join(config.funasr_model_path, model_name)
        )
        logger.info(
            f"ask_model_folder-is_installed path :{os.path.join(config.funasr_model_path, model_name)}"
        )
        return is_installed

    def calc_trans_ds(self, word_count: int) -> int:
        # 计算代币消耗
        return int(word_count * config.trans_qps)


start_tools = StartTools()


# 执行 ffmpeg
def runffmpeg(arg, *, noextname=None, is_box=False, fps=None):
    logger.info(f"runffmpeg-arg={arg}")
    arg_copy = copy.deepcopy(arg)

    if fps:
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-ignore_unknown",
            "-vsync",
            "1",
            "-r",
            f"{fps}",
        ]
    else:
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-ignore_unknown",
            "-vsync",
            f"{config.settings['vsync']}",
        ]
    # 启用了CUDA 并且没有禁用GPU
    # 默认视频编码 libx264 / libx265
    default_codec = f"libx{config.settings['video_codec']}"

    for i, it in enumerate(arg):
        if arg[i] == "-i" and i < len(arg) - 1:
            arg[i + 1] = os.path.normpath(arg[i + 1]).replace("\\", "/")
            if not vail_file(arg[i + 1]):
                raise OSError(f'..{arg[i + 1]} {config.transobj["vlctips2"]}')

    if default_codec in arg and config.video_codec != default_codec:
        if not config.video_codec:
            config.video_codec = get_video_codec()
        for i, it in enumerate(arg):
            if i > 0 and arg[i - 1] == "-c:v":
                arg[i] = config.video_codec

    arg.insert(-1, "-fps_mode")
    arg.insert(-1, "cfr" if fps else "vfr")
    cmd += arg
    print(f"ffmpeg:{cmd=}")
    logger.info(f"runffmpeg-tihuan:{cmd=}")
    if noextname:
        config.queue_novice[noextname] = "ing"
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=True,
            text=True,
            creationflags=0 if sys.platform != "win32" else subprocess.CREATE_NO_WINDOW,
        )
        if noextname:
            config.queue_novice[noextname] = "end"
        return True
    except subprocess.CalledProcessError as e:
        retry = False
        logger.error(f"出错了:{cmd=}")
        logger.error(f"before:{retry=},{arg_copy=}")
        # 处理视频时如果出错，尝试回退
        if cmd[-1].endswith(".mp4"):
            # 存在视频的copy操作时，尝试回退使用重新编码
            if "copy" in cmd:
                for i, it in enumerate(arg_copy):
                    if i > 0 and arg_copy[i - 1] == "-c:v" and it == "copy":
                        arg_copy[i] = (
                            config.video_codec
                            if config.video_codec is not None
                            else default_codec
                        )
                        retry = True
            # 如果不是copy并且也不是 libx264，则替换为libx264编码
            if not retry and config.video_codec != default_codec:
                config.video_codec = default_codec
                # 切换为cpu
                if not is_box:
                    set_process(config.transobj["huituicpu"])
                logger.error("cuda上执行出错，退回到CPU执行")
                for i, it in enumerate(arg_copy):
                    if i > 0 and arg_copy[i - 1] == "-c:v" and it != default_codec:
                        arg_copy[i] = default_codec
                        retry = True
            logger.error(f"after:{retry=},{arg_copy=}")
            if retry:
                return runffmpeg(arg_copy, noextname=noextname, is_box=is_box)
        if noextname:
            config.queue_novice[noextname] = "error"
        logger.error(f"cmd执行出错抛出异常:{cmd=},{str(e.stderr)}")
        raise ValueError(str(e.stderr))
    except Exception as e:
        logger.error(f"执行出错 Exception:{cmd=},{str(e)}")
        raise VideoProcessingError(str(e))


# run ffprobe 获取视频元信息
def runffprobe(cmd):
    print(f"ffprobe:{cmd=}")
    try:
        p = subprocess.run(
            cmd if isinstance(cmd, str) else ["ffprobe"] + cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            text=True,
            check=True,
            creationflags=0 if sys.platform != "win32" else subprocess.CREATE_NO_WINDOW,
        )
        if p.stdout:
            return p.stdout.strip()
        raise VideoProcessingError(str(p.stderr))
    except subprocess.CalledProcessError as e:
        print(f"ffprobe---error{e=},{e.args=}")
        msg = f"ffprobe error,:{str(e.stdout)},{str(e.stderr)}"
        msg = msg.replace("\n", " ")
        raise VideoProcessingError(msg)
    except Exception as e:
        raise VideoProcessingError(f"ffprobe except,{cmd=}:{str(e)}")


# 获取视频信息
def get_video_info(
        mp4_file, *, video_fps=False, video_scale=False, video_time=False, nocache=False
):
    # 如果存在缓存并且没有禁用缓存
    mp4_file = Path(mp4_file).as_posix()
    if not nocache and mp4_file in config.video_cache:
        result = config.video_cache[mp4_file]
    else:
        result = _extracted_from_get_video_info(mp4_file, nocache)
    if video_time:
        return result["time"]
    if video_fps:
        return ["video_fps"]
    if video_scale:
        return result["width"], result["height"]
    return result


# TODO Rename this here and in `get_video_info`
def _extracted_from_get_video_info(mp4_file, nocache):
    out = runffprobe(
        [
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            mp4_file,
        ]
    )
    if out is False:
        raise VideoProcessingError("ffprobe error:dont get video information")
    out = json.loads(out)
    result = {
        "video_fps": 30,
        "video_codec_name": "",
        "audio_codec_name": "aac",
        "width": 0,
        "height": 0,
        "time": 0,
        "streams_len": 0,
        "streams_audio": 0,
    }
    if "streams" not in out or len(out["streams"]) < 1:
        raise VideoProcessingError("ffprobe error:streams is 0")

    if "format" in out and out["format"]["duration"]:
        result["time"] = int(float(out["format"]["duration"]) * 1000)
    for it in out["streams"]:
        result["streams_len"] += 1
        if it["codec_type"] == "video":
            result["video_codec_name"] = it["codec_name"]
            result["width"] = int(it["width"])
            result["height"] = int(it["height"])

            fps_split = it["r_frame_rate"].split("/")
            fps1 = (
                30
                if len(fps_split) != 2 or fps_split[1] == "0"
                else round(int(fps_split[0]) / int(fps_split[1]), 2)
            )
            fps_split = it["avg_frame_rate"].split("/")
            if len(fps_split) != 2 or fps_split[1] == "0":
                fps = fps1
            else:
                fps = round(int(fps_split[0]) / int(fps_split[1]), 2)

            result["video_fps"] = fps if 16 <= fps <= 60 else 30
        elif it["codec_type"] == "audio":
            result["streams_audio"] += 1
            result["audio_codec_name"] = it["codec_name"]
    if not nocache:
        config.video_cache[mp4_file] = result

    return result


# 获取某个视频的时长 s
def get_video_duration(file_path):
    return get_video_info(file_path, video_time=True, nocache=True)


# 获取某个视频的fps
def get_video_fps(file_path):
    return get_video_info(file_path, video_fps=True)


# 获取宽高分辨率
def get_video_resolution(file_path):
    return get_video_info(file_path, video_scale=True)


# 视频转为 mp4格式 nv12 + not h264_cuvid
def conver_mp4(source_file, out_mp4, *, is_box=False):
    video_codec = config.settings["video_codec"]
    return runffmpeg(
        [
            "-y",
            "-i",
            Path(source_file).as_posix(),
            "-c:v",
            f"libx{video_codec}",
            "-c:a",
            "aac",
            "-crf",
            f'{config.settings["crf"]}',
            "-preset",
            "slow",
            out_mp4,
        ],
        is_box=is_box,
    )


# 从原始视频分离出 无声视频 cuda + h264_cuvid
def split_novoice_byraw(source_mp4, novoice_mp4, noextname, lib="copy"):
    cmd = [
        "-y",
        "-i",
        Path(source_mp4).as_posix(),
        "-an",
        "-c:v",
        lib,
        "-crf",
        "0",
        f"{novoice_mp4}",
    ]
    return runffmpeg(cmd, noextname=noextname)


def conver_to_8k(audio, target_audio):
    return runffmpeg(
        [
            "-y",
            "-i",
            Path(audio).as_posix(),
            "-ac",
            "1",
            "-ar",
            "16000",
            Path(target_audio).as_posix(),
        ]
    )


#  背景音乐是wav,配音人声是m4a，都在目标文件夹下，合并后最后文件仍为 人声文件，时长需要等于人声
def backandvocal(backwav, peiyinm4a):
    backwav = Path(backwav).as_posix()
    peiyinm4a = Path(peiyinm4a).as_posix()
    tmpwav = Path(
        (os.environ["TEMP"] or os.environ["temp"]) + f"/{time.time()}-1.m4a"
    ).as_posix()
    tmpm4a = Path(
        (os.environ["TEMP"] or os.environ["temp"]) + f"/{time.time()}.m4a"
    ).as_posix()
    # 背景转为m4a文件,音量降低为0.8
    wav2m4a(
        backwav, tmpm4a, ["-filter:a", f"volume={config.settings['backaudio_volume']}"]
    )
    runffmpeg(
        [
            "-y",
            "-i",
            peiyinm4a,
            "-i",
            tmpm4a,
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2",
            "-ac",
            "2",
            "-c:a",
            "aac",
            tmpwav,
        ]
    )
    shutil.copy2(tmpwav, peiyinm4a)  # 转为 m4a


# wav转为 m4a cuda + h264_cuvid
def wav2m4a(wavfile, m4afile, extra=None):
    cmd = [
        "-y",
        "-i",
        Path(wavfile).as_posix(),
        "-c:a",
        "aac",
        Path(m4afile).as_posix(),
    ]
    if extra:
        cmd = cmd[:3] + extra + cmd[3:]
    return runffmpeg(cmd)


# wav转为 mp3 cuda + h264_cuvid
def wav2mp3(wavfile, mp3file, extra=None):
    cmd = ["-y", "-i", Path(wavfile).as_posix(), Path(mp3file).as_posix()]
    if extra:
        cmd = cmd[:3] + extra + cmd[3:]
    return runffmpeg(cmd)


# m4a 转为 wav cuda + h264_cuvid
def m4a2wav(m4afile, wavfile):
    cmd = [
        "-y",
        "-i",
        Path(m4afile).as_posix(),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-b:a",
        "128k",
        "-c:a",
        "pcm_s16le",
        Path(wavfile).as_posix(),
    ]
    return runffmpeg(cmd)


# 创建 多个视频的连接文件
def create_concat_txt(filelist, filename):
    txt = [f"file '{it}'" for it in filelist]
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(txt))
    return filename


# 多个视频片段连接 cuda + h264_cuvid
def concat_multi_mp4(*, filelist=None, out=None, maxsec=None, fps=None):
    # 创建txt文件
    if filelist is None:
        filelist = []
    txt = config.TEMP_DIR + f"/{time.time()}.txt"
    video_codec = config.settings["video_codec"]
    create_concat_txt(filelist, txt)
    if out:
        out = Path(out).as_posix()
    if maxsec:
        return runffmpeg(
            [
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                txt,
                "-c:v",
                f"libx{video_codec}",
                "-t",
                f"{maxsec}",
                "-crf",
                f'{config.settings["crf"]}',
                "-preset",
                "slow",
                "-an",
                out,
            ],
            fps=fps,
        )
    return runffmpeg(
        [
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            txt,
            "-c:v",
            f"libx{video_codec}",
            "-an",
            "-crf",
            f'{config.settings["crf"]}',
            "-preset",
            "slow",
            out,
        ],
        fps=fps,
    )


# 多个音频片段连接
def concat_multi_audio(*, filelist=None, out=None):
    if filelist is None:
        filelist = []
    if out:
        out = Path(out).as_posix()
    # 创建txt文件
    txt = config.TEMP_DIR + f"/{time.time()}.txt"
    create_concat_txt(filelist, txt)
    return runffmpeg(
        ["-y", "-f", "concat", "-safe", "0", "-i", txt, "-c:a", "aac", out]
    )


# mp3 加速播放 cuda + h264_cuvid
def speed_up_mp3(*, filename=None, speed=1, out=None):
    return runffmpeg(
        ["-y", "-i", Path(filename).as_posix(), "-af", f"atempo={speed}", out]
    )


def show_popup(title, text, parent=None):
    from PySide6.QtGui import QIcon
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QMessageBox

    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setWindowIcon(QIcon(f"{config.rootdir}/videotrans/styles/icon.ico"))
    msg.setText(text)
    msg.addButton(QMessageBox.Yes)
    msg.addButton(QMessageBox.Cancel)
    msg.setWindowModality(Qt.ApplicationModal)  # 设置为应用模态
    msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)  # 置于顶层

    # msg.addButton(a2)
    msg.setIcon(QMessageBox.Information)
    return msg.exec()


"""
print(ms_to_time_string(ms=12030))
-> 00:00:12,030
"""


def ms_to_time_string(*, ms=0, seconds=None):
    # 计算小时、分钟、秒和毫秒
    if seconds is None:
        td = timedelta(milliseconds=ms)
    else:
        td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000

    time_string = f"{hours}:{minutes}:{seconds},{milliseconds}"
    return format_time(time_string, ",")


# 从字幕文件获取格式化后的字幕信息
"""
[
{'line': 13, 'time': '00:01:56,423 --> 00:02:06,423', 'text': '因此，如果您准备好停止沉迷于不太理想的解决方案并开始构建下一个
出色的语音产品，我们已准备好帮助您实现这一目标。深度图。没有妥协。唯一的机会..', 'startraw': '00:01:56,423', 'endraw': '00:02:06,423', 'start_time'
: 116423, 'end_time': 126423},
{'line': 14, 'time': '00:02:06,423 --> 00:02:07,429', 'text': '机会..', 'startraw': '00:02:06,423', 'endraw': '00:02
:07,429', 'start_time': 126423, 'end_time': 127429}
]
"""


# 将字符串或者字幕文件内容，格式化为有效字幕数组对象
# 格式化为有效的srt格式
# content是每行内容，按\n分割的，
def format_srt(content):
    # 去掉空行
    content = [it for it in content if it.strip()]
    if not content:
        return []
    result = []
    maxindex = len(content) - 1
    # 时间格式
    timepat = r"^\s*?\d+:\d+:\d+([\,\.]\d*?)?\s*?-->\s*?\d+:\d+:\d+([\,\.]\d*?)?\s*?$"
    textpat = r"^[,./?`!@#$%^&*()_+=\\|\[\]{}~\s \n-]*$"
    for i, it in enumerate(content):
        # 当前空行跳过
        if not it.strip():
            continue
        it = it.strip()
        if is_time := re.match(timepat, it):
            # 当前行是时间格式，则添加
            result.append({"time": it, "text": list})
        elif i == 0:
            # 当前是第一行，并且不是时间格式，跳过
            continue
        elif (
                re.match(r"^\s*?\d+\s*?$", it)
                and i < maxindex
                and re.match(timepat, content[i + 1])
        ):
            # 当前不是时间格式，不是第一行，并且都是数字，并且下一行是时间格式，则当前是行号，跳过
            continue
        elif len(result) > 0 and not re.match(textpat, it):
            # 当前不是时间格式，不是第一行，（不是行号），并且result中存在数据，则是内容，可加入最后一个数据

            result[-1]["text"].append(it.capitalize())

    # 再次遍历，去掉text为空的
    result = [it for it in result if len(it["text"]) > 0]

    if result:
        for i, it in enumerate(result):
            result[i]["line"] = i + 1
            result[i]["text"] = "\n".join([tx.capitalize() for tx in it["text"]])
            s, e = (it["time"].replace(".", ",")).split("-->")
            s = format_time(s, ",")
            e = format_time(e, ",")
            result[i]["time"] = f"{s} --> {e}"
    return result


def get_subtitle_from_srt(srtfile, *, is_file=True):
    if is_file:
        if os.path.getsize(srtfile) == 0:
            raise ValueError(config.transobj["zimuwenjianbuzhengque"])
        try:
            with open(srtfile, "r", encoding="utf-8") as f:
                content = f.read().strip().splitlines()
        except:
            try:
                with open(srtfile, "r", encoding="gbk") as f:
                    content = f.read().strip().splitlines()
            except Exception as e:
                raise VideoProcessingError(f"get srtfile error:{str(e)}")
    else:
        content = srtfile.strip().splitlines()
    # remove whitespace
    content = [c for c in content if c.strip()]

    if not content:
        raise ValueError("srt content is empty")

    result = format_srt(content)

    # txt 文件转为一条字幕
    if len(result) < 1:
        if is_file and srtfile.endswith(".txt"):
            result = [
                {
                    "line": 1,
                    "time": "00:00:00,000 --> 05:00:00,000",
                    "text": "\n".join(content),
                }
            ]
        else:
            return []

    new_result = []
    line = 1
    for it in result:
        if "text" in it and len(it["text"].strip()) > 0:
            it["line"] = line
            startraw, endraw = it["time"].strip().split("-->")

            startraw = format_time(
                startraw.strip().replace(",", ".").replace("，", ".").replace("：", ":"),
                ".",
            )
            start = startraw.split(":")

            endraw = format_time(
                endraw.strip().replace(",", ".").replace("，", ".").replace("：", ":"),
                ".",
            )
            end = endraw.split(":")

            start_time = int(
                int(start[0]) * 3600000 + int(start[1]) * 60000 + float(start[2]) * 1000
            )
            end_time = int(
                int(end[0]) * 3600000 + int(end[1]) * 60000 + float(end[2]) * 1000
            )
            it["startraw"] = startraw
            it["endraw"] = endraw
            it["start_time"] = start_time
            it["end_time"] = end_time
            new_result.append(it)
            line += 1
    if not new_result:
        raise VideoProcessingError(config.transobj["zimuwenjianbuzhengque"])

    return new_result


# 将 时:分:秒,|.毫秒格式为  aa:bb:cc,|.ddd形式
def format_time(s_time="", separate=","):
    if not s_time.strip():
        return f"00:00:00{separate}000"
    s_time = s_time.strip()
    hou, _min, sec = "00", "00", f"00{separate}000"
    tmp = s_time.split(":")
    if len(tmp) >= 3:
        hou = tmp[-3].strip()
        _min = tmp[-2].strip()
        sec = tmp[-1].strip()
    elif len(tmp) == 2:
        _min = tmp[0].strip()
        sec = tmp[1].strip()
    elif len(tmp) == 1:
        sec = tmp[0].strip()

    if re.search(r",|\.", str(sec)):
        sec, ms = re.split(r",|\.", str(sec))
        sec = sec.strip()
        ms = ms.strip()
    else:
        ms = "000"
    hou = hou if hou != "" else "00"
    if len(hou) < 2:
        hou = f"0{hou}"
    hou = hou[-2:]

    _min = _min if _min != "" else "00"
    if len(_min) < 2:
        _min = f"0{_min}"
    _min = _min[-2:]

    sec = sec if sec != "" else "00"
    if len(sec) < 2:
        sec = f"0{sec}"
    sec = sec[-2:]

    ms_len = len(ms)
    if ms_len < 3:
        for _ in range(3 - ms_len):
            ms = f"0{ms}"
    ms = ms[-3:]
    return f"{hou}:{_min}:{sec}{separate}{ms}"


# 判断 novoice.mp4是否创建好
def is_novoice_mp4(novoice_mp4, noextname):
    # 预先创建好的
    # 判断novoice_mp4是否完成
    t = 0
    if noextname not in config.queue_novice and vail_file(novoice_mp4):
        return True
    if noextname in config.queue_novice and config.queue_novice[noextname] == "end":
        return True
    last_size = 0
    while True:
        if config.current_status != "ing":
            raise VideoProcessingError("stop")
        if vail_file(novoice_mp4):
            current_size = os.path.getsize(novoice_mp4)
            if 0 < last_size == current_size and t > 600:
                return True
            last_size = current_size

        if noextname not in config.queue_novice:
            msg = f"{noextname} split no voice videoerror:{ config.queue_novice=}"
            raise ValueError(msg)
        if config.queue_novice[noextname] == "error":
            msg = f"{noextname} split no voice videoerror"
            raise ValueError(msg)

        if config.queue_novice[noextname] == "ing":
            size = f"{round(last_size / 1024 / 1024, 2)}MB" if last_size > 0 else ""
            set_process(
                f"{noextname} {'分离音频和画面' if config.defaulelang == 'zh' else 'spilt audio and video'} {size}"
            )
            time.sleep(3)
            t += 3
            continue
        return True


def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)


# 从视频中切出一段时间的视频片段 cuda + h264_cuvid
def cut_from_video(*, ss="", to="", source="", pts="", out="", fps=None):
    video_codec = config.settings["video_codec"]
    cmd1 = ["-y", "-ss", format_time(ss, ".")]
    if to != "":
        cmd1.append("-to")
        cmd1.append(format_time(to, "."))  # 如果开始结束时间相同，则强制持续时间1s)
    cmd1.append("-i")
    cmd1.append(source)

    if pts:
        cmd1.append("-vf")
        cmd1.append(f"setpts={pts}*PTS")
    cmd = cmd1 + [
        "-c:v",
        f"libx{video_codec}",
        "-an",
        "-crf",
        f'{config.settings["crf"]}',
        "-preset",
        "slow",
        f"{out}",
    ]
    return runffmpeg(cmd, fps=fps)


# 从音频中截取一个片段
def cut_from_audio(*, ss, to, audio_file, out_file):
    cmd = [
        "-y",
        "-i",
        audio_file,
        "-ss",
        format_time(ss, "."),
        "-to",
        format_time(to, "."),
        "-ar",
        "16000",
        out_file,
    ]
    return runffmpeg(cmd)


# 工具箱写入日志队列
def set_process_box(text, type="logs", *, func_name=""):
    set_process(text, type, qname="box", func_name=func_name)


# 综合写入日志，默认sp界面
def set_process(
        text, type="logs", *, qname="sp", func_name="", btnkey="", nologs=False
):
    with contextlib.suppress(Exception):
        if text:
            if not nologs:
                if type == "error":
                    logger.error(text)
                else:
                    logger.info(text)

            # 移除html
            if type == "error":
                text = re.sub(r"</?!?[a-zA-Z]+[^>]*?>", "", text, re.I | re.M | re.S)
                text = text.replace("\\n", " ").strip()

        if qname == "sp":
            config.queue_logs.put_nowait({"text": text, "type": type, "btnkey": btnkey})
        elif qname == "box":
            config.queuebox_logs.put_nowait(
                {"text": text, "type": type, "func_name": func_name}
            )
        else:
            print(f"[{type}]: {text}")


# 判断是否需要重命名，如果需要则重命名并转移
def rename_move(file, *, is_dir=False):
    patter = r'[ \s`"\'!@#$%^&*()=+,?\|{}\[\]]+'
    if re.search(patter, file):
        if is_dir:
            os.makedirs(config.homedir + "/target_dir", exist_ok=True)
            return True, config.homedir + "/target_dir", False
        dirname = os.path.dirname(file)
        basename = os.path.basename(file)
        # 目录不规则，迁移目录
        if re.search(patter, dirname):
            basename = re.sub(patter, "", basename, 0, re.I)
            basename = basename.replace(":", "")
            os.makedirs(f"{config.homedir}/rename", exist_ok=True)
            newfile = config.homedir + f"/rename/{basename}"
        else:
            # 目录规则仅名称不规则，只修改名称
            basename = re.sub(patter, "", basename, 0, re.I)
            basename = basename.replace(":", "")
            newfile = dirname + "/" + basename
        shutil.copy2(file, newfile)
        return True, newfile, basename
    return False, False, False


# 获取音频时长
def get_audio_time(audio_file):
    # 如果存在缓存并且没有禁用缓存
    out = runffprobe(
        [
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            audio_file,
        ]
    )
    if out is False:
        raise ValueError("ffprobe error:dont get video information")
    out = json.loads(out)
    return float(out["format"]["duration"])


def kill_ffmpeg_processes():
    import platform
    import signal
    import getpass

    with contextlib.suppress(Exception):
        system_platform = platform.system()
        current_user = getpass.getuser()

        if system_platform == "Windows":
            subprocess.call(
                f'taskkill /F /FI "USERNAME eq {current_user}" /IM ffmpeg.exe',
                shell=True,
            )
        elif system_platform in ["Linux", "Darwin"]:
            process = subprocess.Popen(
                ["ps", "-U", current_user], stdout=subprocess.PIPE
            )
            out, _ = process.communicate()

            for line in out.splitlines():
                if b"ffmpeg" in line:
                    pid = int(line.split(None, 1)[0])
                    os.kill(pid, signal.SIGKILL)


# 从 google_url 中获取可用地址


def remove_qsettings_data(organization="Jameson", application="VideoTranslate"):
    from PySide6.QtCore import QSettings
    import platform

    # Create a QSettings object with the specified organization and application
    settings = QSettings(organization, application)

    # Clear all settings in QSettings
    settings.clear()
    settings.sync()  # Make sure changes are written to the disk

    # Determine if the platform is Windows
    if platform.system() == "Windows":
        # On Windows, the settings are stored in the registry, so no further action is needed
        return
    with contextlib.suppress(Exception):
        # On MacOS and Linux, settings are usually stored in a config file within the user's home directory
        config_dir = os.path.join(os.path.expanduser("~"), ".config", organization)
        config_file_path = os.path.join(config_dir, f"{application}.ini")

        # Check if the config file exists and remove it
        if os.path.isfile(config_file_path):
            os.remove(config_file_path)
        # If the whole directory for the organization should be removed, you would use shutil.rmtree as follows
        # Warning: This will remove all settings for all applications under this organization
        elif os.path.isdir(config_dir):
            shutil.rmtree(config_dir, ignore_errors=True)


def detect_media_type(file_path: str):
    # 判断媒体文件是音频还是视频
    try:
        # 使用ffprobe获取文件信息
        command = [
            "ffprobe",  # ff_path,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            file_path,
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

        # 解析JSON输出
        file_info = json.loads(result.stdout)

        # 检查流信息
        for stream in file_info.get("streams", []):
            if stream["codec_type"] == "video":
                return "video"
            elif stream["codec_type"] == "audio":
                return "audio"

        # 如果没有找到视频或音频流
        return "unknown"

    except Exception as e:
        print(f"Error detecting media type: {e}")
        return "unknown"


def get_default_documents_path() -> Union[str, Path]:
    """
    返回当前操作系统的默认文档文件夹路径。

    Returns:
        Union[str, Path]: 默认文档文件夹的路径。
                          返回类型可能是字符串或 Path 对象，
                          具体取决于操作系统和环境变量。
    """
    if sys.platform.startswith("win"):
        # Windows
        return str(Path.home() / "Documents")
    elif sys.platform.startswith("darwin"):
        # macOS
        return str(Path.home() / "Documents")
    elif sys.platform.startswith("linux"):
        if xdg_documents := os.environ.get("XDG_DOCUMENTS_DIR"):
            return xdg_documents
        else:
            return str(Path.home() / "Documents")
    else:
        # 其他操作系统
        return str(Path.home())  # 默认返回用户主目录


class VideoFormatInfo(BaseModel):
    # 定义数据类型,是一个字典,里面有key a,a的数据类型为str
    """
        {
      'raw_name': 'F:/ski/国外教学翻译/HYPER FOCUS - Teton Brown skis Jackson Hole.mp4',
      'raw_dirname': 'F:/ski/国外教学翻译',
      'raw_basename': 'HYPER FOCUS - Teton Brown skis Jackson Hole.mp4',
      'raw_noextname': 'HYPER FOCUS - Teton Brown skis Jackson Hole',
      'raw_ext': 'mp4',
      'codec_type': 'video',
      'output': 'D:/dcode/lin_trans/result/5f421d80a8a6a9211a18e5ec06ee21e3',
      'wav_dirname': 'D:/dcode/lin_trans/result/5f421d80a8a6a9211a18e5ec06ee21e3/HYPER FOCUS - Teton Brown skis Jackson Hole.wav',
      'srt_dirname': 'D:/dcode/lin_trans/result/5f421d80a8a6a9211a18e5ec06ee21e3/HYPER FOCUS - Teton Brown skis Jackson Hole.srt',
      'unid': '5f421d80a8a6a9211a18e5ec06ee21e3',
      'source_mp4': 'F:/ski/国外教学翻译/HYPER FOCUS - Teton Brown skis Jackson Hole.mp4',
      'work_type': 'asr'
    }
    """
    raw_name: str = Field(..., description="原始文件路径")
    raw_dirname: str = Field(..., description="原始文件所在原始目录")
    raw_basename: str = Field(..., description="原始文件原始名字带后缀")
    raw_noextname: str = Field(..., description="原始文件名字不带后缀")
    raw_ext: str = Field(..., description="原始后缀不带 .")
    codec_type: str = Field(..., description="视频或音频")
    output: str = Field(..., description="最终存放的路径")
    wav_dirname: str = Field(..., description="ff处理完wav文件路径")
    media_dirname: Optional[str] = Field(..., description="媒体路径")
    srt_dirname: str = Field(..., description="funasr处理完srt文件路径")
    unid: str = Field(..., description="文件指纹")
    source_mp4: str = Field(..., description="任务文件路径，原始文件路径")
    work_type: Optional[WORK_TYPE] = Field(
        default=None, description="任务类型，asr、trans 可选字段"
    )


def format_job_msg(name: str, out, work_type: WORK_TYPE) -> VideoFormatInfo:
    """
    格式化任务信息

    Args:
        name: #需要处理的文件路径，如'C:/Users/gaosh/Videos/pyvideotrans/rename/BetterCarvedTurnsUsingTheSwordsDrill.mp4'
        out: #输出目录，result路径
        work_type: #任务类型，asr、trans、asr+trans

    Returns:
        VideoFormatInfo: 视频格式化信息

    """
    raw_pathlib = Path(name)
    raw_basename = raw_pathlib.name
    raw_noextname = raw_pathlib.stem
    ext = raw_pathlib.suffix
    raw_dirname = raw_pathlib.parent.resolve().as_posix()

    h = hashlib.md5()
    h.update(name.encode("utf-8"))
    h.update(config.params.get("source_module_name").encode("utf-8"))
    current_time = str(time.time()).encode("utf-8")
    h.update(current_time)

    unid = h.hexdigest()
    output_path = out / unid
    wav_path = output_path / f"{raw_noextname}.wav"
    srt_path = output_path / f"{raw_noextname}.srt"
    srt_finally_path = srt_path.as_posix()
    output_path.mkdir(parents=True, exist_ok=True)
    # 判断文件是视频还是音频
    media_type = detect_media_type(name)
    if work_type in (WORK_TYPE.ASR, WORK_TYPE.ASR_TRANS, WORK_TYPE.CLOUD_ASR):
        media_dirname = name
        wav_finally_path = wav_path.as_posix()
    elif work_type == WORK_TYPE.TRANS:
        media_dirname = ""
        wav_finally_path = ""
    else:
        logger.error(f"unknown work_type: {work_type}")
    return VideoFormatInfo(
        raw_name=name,
        raw_dirname=raw_dirname,
        raw_basename=raw_basename,
        raw_noextname=raw_noextname,
        raw_ext=ext[1:],
        codec_type=media_type,
        output=output_path.as_posix(),
        wav_dirname=wav_finally_path,
        srt_dirname=srt_finally_path,
        media_dirname=media_dirname,
        unid=unid,
        source_mp4=name,
        work_type=work_type,
    )


def change_job_format(asr_task_finished: VideoFormatInfo) -> VideoFormatInfo:
    new_task = copy.deepcopy(asr_task_finished)
    raw_pathlib = Path(asr_task_finished.srt_dirname)
    new_task.raw_name = asr_task_finished.srt_dirname
    new_task.raw_dirname = raw_pathlib.parent.resolve().as_posix()
    new_task.raw_basename = raw_pathlib.name
    new_task.raw_noextname = raw_pathlib.stem
    new_task.raw_ext = raw_pathlib.suffix[1:]
    new_task.work_type = WORK_TYPE.ASR_TRANS
    return new_task


def open_dir(self, dirname=None):
    if not dirname:
        return
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices

    dirname = dirname.strip()
    if not os.path.isdir(dirname):
        dirname = os.path.dirname(dirname)
    if not dirname or not os.path.isdir(dirname):
        return
    QDesktopServices.openUrl(QUrl.fromLocalFile(dirname))


def vail_file(file=None) -> bool:
    # 检验文件是否存在，大小是否大于0
    if not file:
        return False
    p = Path(file)
    if not p.exists() or not p.is_file():
        return False
    if p.stat().st_size < 1:
        return False
    return True


# 获取最终视频应该输出的编码格式
def get_video_codec():
    plat = platform.system()
    # 264 / 265
    video_codec = int(config.settings["video_codec"])
    hhead = "hevc" if video_codec != 264 else "h264"
    mp4_test = config.rootdir + "/videotrans/styles/no-remove.mp4"
    if not Path(mp4_test).is_file():
        return f"libx{video_codec}"
    mp4_target = config.TEMP_DIR + "/test.mp4"
    codec = ""
    if plat in ("Windows", "Linux"):
        import torch

        if torch.cuda.is_available():
            codec = f"{hhead}_nvenc"
        elif plat == "Windows":
            codec = f"{hhead}_qsv"
        elif plat == "Linux":
            codec = f"{hhead}_vaapi"
    elif plat == "Darwin":
        codec = f"{hhead}_videotoolbox"

    if not codec:
        return f"libx{video_codec}"

    try:
        Path(config.TEMP_DIR).mkdir(exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-ignore_unknown",
                "-i",
                mp4_test,
                "-c:v",
                codec,
                mp4_target,
            ],
            check=True,
            creationflags=0 if sys.platform != "win32" else subprocess.CREATE_NO_WINDOW,
        )
    except Exception:
        if sys.platform == "win32":
            try:
                codec = f"{hhead}_amf"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-hide_banner",
                        "-ignore_unknown",
                        "-i",
                        mp4_test,
                        "-c:v",
                        codec,
                        mp4_target,
                    ],
                    check=True,
                    creationflags=(
                        0 if sys.platform != "win32" else subprocess.CREATE_NO_WINDOW
                    ),
                )
            except Exception:
                codec = f"libx{video_codec}"
    return codec


# 设置ass字体格式
def set_ass_font(srtfile=None):
    if not os.path.exists(srtfile) or os.path.getsize(srtfile) == 0:
        return os.path.basename(srtfile)
    runffmpeg(["-y", "-i", srtfile, f"{srtfile}.ass"])
    assfile = f"{srtfile}.ass"
    with open(assfile, "r", encoding="utf-8") as f:
        ass_str = f.readlines()

    for i, it in enumerate(ass_str):
        if it.find("Style: ") == 0:
            ass_str[
                i
            ] = "Style: Default,{fontname},{fontsize},{fontcolor},&HFFFFFF,{fontbordercolor},&H0,0,0,0,0,100,100,0,0,1,1,0,2,10,10,{subtitle_bottom},1".format(
                fontname=config.settings["fontname"],
                fontsize=config.settings["fontsize"],
                fontcolor=config.settings["fontcolor"],
                fontbordercolor=config.settings["fontbordercolor"],
                subtitle_bottom=config.settings["subtitle_bottom"],
            )
            break

    with open(assfile, "w", encoding="utf-8") as f:
        f.write("".join(ass_str))
    return os.path.basename(assfile)


# 根据原始语言list中每个项字数，所占所字数比例，将翻译结果list target_list 按照同样比例切割
# urgent是中日韩泰语言，按字符切割，否则按标点符号切割
def format_result(source_list, target_list, target_lang="zh"):
    source_len = []
    source_total = 0
    for it in source_list:
        it_len = len(it.strip())
        source_total += it_len
        source_len.append(it_len)
    target_str = ".".join(target_list).strip()
    target_total = len(target_str)
    target_len = [int(target_total * num / source_total) for num in source_len]
    # 开始截取文字
    result = []
    start = 0
    # 如果是中日韩泰语言，直接按字切割
    if (
            len(target_lang) < 6 and target_lang[:2].lower() in ["zh", "ja", "ko", "th"]
    ) or (
            len(target_lang) > 5
            and target_lang[:3].lower() in ["sim", "tra", "jap", "kor", "tha"]
    ):
        for num in target_len:
            text = target_str[start: start + num]
            start = start + num
            result.append(text)
        return result

    # 如果其他语言，需要找到最近的标点或空格
    flag = [
        ".",
        " ",
        ",",
        "!",
        "?",
        "-",
        "_",
        "~",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        "<",
        ">",
        "/",
        ";",
        ":",
        "|",
    ]
    for num in target_len:
        lastpos = start + num
        text = target_str[start:lastpos]
        if num < 3 or text[-1] in flag:
            start = start + num
            result.append(text)
            continue
        # 倒退3个到前进10个寻找标点
        offset = -2
        while offset < 5:
            lastpos += offset
            # 如果达到了末尾或者找到了标点则切割
            if lastpos >= target_total or target_str[lastpos] in flag:
                text = target_str[start: lastpos + 1] if start < target_total else ""
                start = lastpos + 1
                result.append(text)
                break
            offset += 1
        # 已找到切割点
        if offset < 5:
            continue
        # 没找到分割标点，强制截断
        text = target_str[start: start + num] if start < target_total else ""
        start = start + num
        result.append(text)
    print(f"{result=}")
    return result


def list_model_files(model_dir: str = None) -> list:
    """
    遍历指定的model文件夹,输出所有文件名(不带后缀)

    Args:
        model_dir (str, optional): model文件夹的路径. 默认为None,此时使用配置中的路径.

    Returns:
        list: 包含所有文件名(不带后缀)的列表
    """
    if model_dir is None:
        model_dir = config.root_path / "models"

    model_files = []
    model_list = config.model_list

    for root, dirs, files in os.walk(model_dir):
        for file in files:
            # 使用 Path 对象来处理文件路径,这样可以跨平台使用
            file_path = Path(root) / file
            # 获取文件名(不带后缀)
            file_name = file_path.stem
            model_files.append(file_name)

    return model_files


if __name__ == "__main__":
    print(start_tools.match_model_name("多语言模型"))
