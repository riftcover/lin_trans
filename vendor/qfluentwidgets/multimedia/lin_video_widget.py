# coding:utf-8
import re
from datetime import timedelta
from bisect import bisect_right

from PySide6.QtCore import Qt, QUrl, QSizeF
from PySide6.QtGui import QPainter, QFont
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import QWidget, QGraphicsView, QVBoxLayout, QGraphicsScene, QSpacerItem, QSizePolicy, QGraphicsTextItem, QGraphicsDropShadowEffect

from nice_ui.ui.style import SubtitleTable
from ..common.style_sheet import FluentStyleSheet
from .media_play_bar import LinMediaPlayBar
from nice_ui.configure import config

class SrtParser:
    def __init__(self, srt_file):
        self.subtitles = []
        self.parse_srt(srt_file)

    def parse_srt(self, srt_file):
        with open(srt_file, 'r', encoding='utf-8') as file:
            content = file.read()

        subtitle_blocks = content.strip().split('\n\n')
        for block in subtitle_blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                time_line = lines[1]
                text = '\n'.join(lines[2:])
                start_time, end_time = self.parse_time(time_line)
                self.subtitles.append((start_time, end_time, text))

    def parse_time(self, time_line):
        pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3})'
        start, end = time_line.split(' --> ')
        start_match = re.match(pattern, start)
        end_match = re.match(pattern, end)

        start_time = timedelta(hours=int(start_match.group(1)), minutes=int(start_match.group(2)), seconds=int(start_match.group(3)),
                               milliseconds=int(start_match.group(4)))
        end_time = timedelta(hours=int(end_match.group(1)), minutes=int(end_match.group(2)), seconds=int(end_match.group(3)),
                             milliseconds=int(end_match.group(4)))

        return start_time, end_time

    def get_subtitle(self, current_time):
        for start, end, text in self.subtitles:
            if start <= current_time <= end:
                return text
        return ""


class LinVideoWidget(QWidget):
    """ Video widget """

    def __init__(self,subtitle_table:SubtitleTable=None,subtitles=None, parent=None):
        super().__init__(parent)
        self.subtitle_table = subtitle_table
        self.subtitles = subtitles
        self.vBoxLayout = QVBoxLayout(self)
        self.graphicsView = QGraphicsView(self)
        self.videoItem = QGraphicsVideoItem()
        self.graphicsScene = QGraphicsScene(self)
        self.playBar = LinMediaPlayBar(self)
        # self.playBar = StandardMediaPlayBar(self)
        config.logger.debug(f'self.playBar.size()={self.playBar.size()}')

        # 将图形视图与图形场景关联，添加视频项到场景中，并设置滚动条策略和渲染提示。
        self.graphicsView.setScene(self.graphicsScene)
        self.graphicsScene.addItem(self.videoItem)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        # 添加字幕项
        self.subtitleItem = QGraphicsTextItem()
        self.subtitleItem.setDefaultTextColor(Qt.white)
        self.subtitleItem.setFont(QFont("Arial", 14))
        self.graphicsScene.addItem(self.subtitleItem)

        # 创建并设置阴影效果
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(0)  # 不模糊，纯黑边
        shadow_effect.setColor(Qt.black)  # 阴影颜色为黑色
        shadow_effect.setOffset(1, 1)  # 阴影偏移量，调整黑边的粗细
        self.subtitleItem.setGraphicsEffect(shadow_effect)

        self.graphicsScene.addItem(self.subtitleItem)

        # 创建一个弹性空间，它会吸收额外的垂直空间
        spacer = QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.vBoxLayout.addWidget(self.graphicsView)
        # self.vBoxLayout.addLayout(self.videoItem)
        self.vBoxLayout.addSpacing(0)
        self.vBoxLayout.addWidget(self.playBar)
        # self.vBoxLayout.addSpacerItem(spacer)  # 添加固定间距
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.player.setVideoOutput(self.videoItem)
        FluentStyleSheet.MEDIA_PLAYER.apply(self)

        # 预处理字幕数据
        self.subtitles = subtitles

        # 连接播放器的positionChanged信号到更新字幕的方法
        # self.player.positionChanged.connect(self.update_subtitle)
        # 目前巨快，如果性能不好尝试降低
        self.player.positionChanged.connect(self.update_subtitle_from_table)

        # # 监听 SubtitleTable 的变化
        self.setup_subtitle_change_listeners()



    def setup_subtitle_change_listeners(self):
        """ 监听 SubtitleTable 内容变化：字幕改变，字幕行变化，字幕时间变化 """
        if self.subtitle_table is None:
            return
        self.subtitle_table.tableChanged.connect(self.on_subtitle_changed)


    def on_subtitle_changed(self,new_srt):
        """ 当字幕改变时调用 """
        config.logger.debug("on_subtitle_changed")
        self.subtitles = new_srt


    def setVideo(self, url: QUrl):
        """ set the video to play
            播放器默认显示第一帧
        """
        self.player.setSource(url)
        self.player.play()
        self.player.pause()

    def setSrtFile(self, srt_file_path: str):
        """ 设置SRT文件并解析 """
        self.subtitles = self.parse_srt(srt_file_path)

    def parse_srt(self, srt_file_path: str):
        """ 解析SRT文件 """
        with open(srt_file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        """
        1.添加了re.DOTALL标志，使得.可以匹配换行符。
        2.使用(?:\n\n|\Z)作为每个字幕块的结束标记，其中\Z表示字符串的结尾。
        3.这个新的正则表达式将能够匹配新的字幕格式，即使字幕文本只有一行。它会捕获字幕序号、开始时间、结束时间和字幕文本，无论文本是单行还是多行。
        """
        subtitle_pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?:\n\n|\Z)', re.DOTALL)
        subtitles = []

        for match in subtitle_pattern.finditer(content):
            # 格式：
            # <re.Match object; span=(0, 60), match="1\n00:00:00,166 --> 00:00:01,166\nwe're going to >
            # config.logger.debug(f'match={match}')
            start_time = self.time_to_milliseconds(match.group(2))
            end_time = self.time_to_milliseconds(match.group(3))
            text = match.group(4).strip()
            # config.logger.debug(f'text={text}')
            subtitles.append((start_time, end_time, text))

        return subtitles

    def time_to_milliseconds(self, time_str):
        """ 将时间字符串转换为毫秒 """
        h, m, s = time_str.split(':')
        s, ms = s.split(',')
        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)

    def update_subtitle(self, position):
        """ 根据当前播放位置更新字幕，这个是加载srt文件使用的 """
        current_subtitle = ""
        for start, end, text in self.subtitles:
            if start <= position <= end:
                current_subtitle = text
                break

        self.subtitleItem.setPlainText(current_subtitle)
        self.position_subtitle()

    def update_subtitle_from_table(self, position):
        """ 根据当前播放位置更新字幕，这个是读取table中的字幕数据使用的 """
        position_ms = position

        # 使用二分查找找到当前时间对应的字幕
        index = bisect_right(self.subtitles, (position_ms,)) - 1
        if 0 <= index < len(self.subtitles):
            start_ms, end_ms, subtitle_text = self.subtitles[index]
            if start_ms <= position_ms <= end_ms:
                self.subtitleItem.setPlainText(subtitle_text)
            # else:
            #     self.subtitleItem.setPlainText("")
        # else:
        #     self.subtitleItem.setPlainText("")

        self.position_subtitle()

    def position_subtitle(self):
        """ 调整字幕位置 """
        # todo: 字幕位置应该根据视频大小自动调整，目前不准确
        video_rect = self.videoItem.boundingRect()
        subtitle_rect = self.subtitleItem.boundingRect()

        x = (video_rect.width() - subtitle_rect.width()) / 2
        y = video_rect.height() - subtitle_rect.height() - 20  # 20是底部边距

        self.subtitleItem.setPos(x, y)

    def play(self):
        self.playBar.play()

    def pause(self):
        self.playBar.pause()

    def stop(self):
        self.playBar.pause()

    def togglePlayState(self):
        """ toggle play state """
        if self.player.isPlaying():
            self.pause()
        else:
            self.play()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.fitInView()

    def fitInView(self):
        # 调整 graphicsView 的大小以填充除了 playBar 和间距之外的所有空间
        # available_height = self.height() - self.playBar.height() - 5  # 5 是间距高度
        config.logger.debug(f'self.graphicsView.size()={self.graphicsView.size()}')
        self.videoItem.setSize(QSizeF(self.graphicsView.size()))
        # self.graphicsView.fitInView(self.videoItem, Qt.KeepAspectRatio)

    @property
    def player(self):

        return self.playBar.player