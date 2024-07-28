# coding:utf-8
import re
from datetime import timedelta
from bisect import bisect_right

from PySide6.QtCore import Qt, Signal, QUrl, QSizeF, QTimer, QEvent
from PySide6.QtGui import QPainter, QFont
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import QWidget, QGraphicsView, QVBoxLayout, QGraphicsScene, QSpacerItem, QSizePolicy, QGraphicsTextItem

from nice_ui.ui.style import LTimeEdit, SubtitleTable
from ..common.style_sheet import FluentStyleSheet
from .media_play_bar import StandardMediaPlayBar, SimpleMediaPlayBar, LinMediaPlayBar


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

    def __init__(self,subtitle_table:SubtitleTable, parent=None):
        super().__init__(parent)
        self.subtitle_table = subtitle_table
        self.vBoxLayout = QVBoxLayout(self)
        self.graphicsView = QGraphicsView(self)
        self.videoItem = QGraphicsVideoItem()
        self.graphicsScene = QGraphicsScene(self)
        #todo：bar调整样式
        self.playBar = LinMediaPlayBar(self)

        self.graphicsView.setScene(self.graphicsScene)
        self.graphicsScene.addItem(self.videoItem)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        # 添加字幕项
        self.subtitleItem = QGraphicsTextItem()
        self.subtitleItem.setDefaultTextColor(Qt.white)
        self.subtitleItem.setFont(QFont("Arial", 16))
        self.graphicsScene.addItem(self.subtitleItem)

        # 创建一个弹性空间，它会吸收额外的垂直空间
        spacer = QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.vBoxLayout.addWidget(self.graphicsView)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.playBar)
        # self.vBoxLayout.addSpacerItem(spacer)  # 添加固定间距
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.player.setVideoOutput(self.videoItem)
        FluentStyleSheet.MEDIA_PLAYER.apply(self)

        # 预处理字幕数据
        self.subtitles = []
        self.process_subtitles()

        # 连接播放器的positionChanged信号到更新字幕的方法
        # self.player.positionChanged.connect(self.update_subtitle)
        # 目前巨快，如果性能不好尝试降低
        self.player.positionChanged.connect(self.update_subtitle_from_table)

    def process_subtitles(self):
        """ 预处理字幕数据 """
        for row in range(self.subtitle_table.rowCount()):
            time_widget = self.subtitle_table.cellWidget(row, 3)
            start_time = time_widget.findChild(LTimeEdit, "start_time")
            end_time = time_widget.findChild(LTimeEdit, "end_time")

            start_ms = self.time_to_milliseconds(start_time.time().toString("HH:mm:ss,zzz"))
            end_ms = self.time_to_milliseconds(end_time.time().toString("HH:mm:ss,zzz"))

            subtitle_widget = self.subtitle_table.cellWidget(row, 4)
            subtitle_text = subtitle_widget.toPlainText()

            self.subtitles.append((start_ms, end_ms, subtitle_text))

        # 按开始时间排序
        self.subtitles.sort(key=lambda x: x[0])

    def setVideo(self, url: QUrl):
        """ set the video to play
            立即暂停以显示第一帧
        """
        self.player.setSource(url)
        self.player.play()
        self.player.pause()
        self.fitInView()

    def setSrtFile(self, srt_file_path: str):
        """ 设置SRT文件并解析 """
        self.subtitles = self.parse_srt(srt_file_path)

    def parse_srt(self, srt_file_path: str):
        """ 解析SRT文件 """
        with open(srt_file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        subtitle_pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.*\n?)*?)(?:\n\n|$)')
        subtitles = []

        for match in subtitle_pattern.finditer(content):
            start_time = self.time_to_milliseconds(match.group(2))
            end_time = self.time_to_milliseconds(match.group(3))
            text = match.group(4).strip()
            subtitles.append((start_time, end_time, text))

        return subtitles

    def time_to_milliseconds(self, time_str):
        """ 将时间字符串转换为毫秒 """
        h, m, s = time_str.split(':')
        s, ms = s.split(',')
        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)

    def update_subtitle(self, position):
        """ 根据当前播放位置更新字幕 """
        current_subtitle = ""
        for start, end, text in self.subtitles:
            if start <= position <= end:
                current_subtitle = text
                break

        self.subtitleItem.setPlainText(current_subtitle)
        self.position_subtitle()

    def update_subtitle_from_table(self, position):
        """ 根据当前播放位置更新字幕 """
        position_ms = position

        # 使用二分查找找到当前时间对应的字幕
        index = bisect_right(self.subtitles, (position_ms,)) - 1
        if 0 <= index < len(self.subtitles):
            start_ms, end_ms, subtitle_text = self.subtitles[index]
            if start_ms <= position_ms <= end_ms:
                self.subtitleItem.setPlainText(subtitle_text)
            else:
                self.subtitleItem.setPlainText("")
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
        self.videoItem.setSize(QSizeF(self.graphicsView.size()))
        # self.graphicsView.fitInView(self.videoItem, Qt.KeepAspectRatio)

    @property
    def player(self):

        return self.playBar.player