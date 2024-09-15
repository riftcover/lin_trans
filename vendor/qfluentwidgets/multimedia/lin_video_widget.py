# coding:utf-8
import re
from datetime import timedelta
from bisect import bisect_right

from PySide6.QtCore import Qt, QUrl, QSizeF
from PySide6.QtGui import QPainter, QFont
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import QWidget, QGraphicsView, QVBoxLayout, QGraphicsScene, QGraphicsTextItem, QGraphicsDropShadowEffect

from components.widget.subedit import SubtitleTable
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

    def __init__(self, subtitle_table: SubtitleTable = None, subtitles=None, parent=None):
        super().__init__(parent)
        self.subtitle_table = subtitle_table
        self.subtitles = subtitles
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)  # 移除部件之间的间距
        self.graphicsView = QGraphicsView(self)
        self.videoItem = QGraphicsVideoItem()
        self.graphicsScene = QGraphicsScene(self)
        self.playBar = LinMediaPlayBar(self)
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

        self.vBoxLayout.addWidget(self.graphicsView)
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

    def fitInView(self):
        """
        这个方法的目的是确保视频在图形视图中正确显示，填满可用空间，同时保持其原始宽高比。
        这对于响应窗口大小变化或初始化视频显示时非常有用，可以保证视频始终以最佳方式呈现。

        在某些情况下，没有 fitInView 方法，视频也可能看起来匹配。但是，添加这段代码有几个重要的好处：
        1. 确保视频比例正确：
            Qt.KeepAspectRatio 参数保证视频不会被拉伸或压缩，始终保持正确的宽高比。
            没有这个方法，视频可能会在某些窗口大小下变形。
        2. 适应不同大小的视频：
            对于不同分辨率和比例的视频，这个方法可以自动调整显示，确保视频始终完整可见。
        3. 响应窗口大小变化：
            当用户调整窗口大小时，fitInView 可以确保视频正确重新缩放和定位。
        4. 处理高DPI显示：
        在高DPI显示器上，这个方法有助于正确计算和显示视频大小。
        5. 优化性能：
            通过精确设置场景矩形（setSceneRect），可以优化渲染性能，因为QGraphicsView只需要关注必要的区域。
        6. 一致的用户体验：
        无论视频源如何，都能提供一致的显示效果，增强用户体验。
        7. 处理边缘情况：
            对于特别小或特别大的视频，或者非标准比例的视频，这个方法可以确保它们都能正确显示。
        """

        # 设置 videoItem（视频项）的大小，使其与 graphicsView（图形视图）的大小相同。
        # QSizeF 创建一个浮点精度的大小对象，基于 graphicsView 的当前大小。
        # 这确保视频项填满整个图形视图区域。
        self.videoItem.setSize(QSizeF(self.graphicsView.size()))
        """
        设置图形视图的场景矩形，使其与视频项的边界矩形相匹配。
        boundingRect() 返回视频项的边界矩形。
        这确保场景大小正好包含整个视频项。
        """
        self.graphicsView.setSceneRect(self.videoItem.boundingRect())
        """
        调整图形视图的视口，使视频项完全可见。
        Qt.KeepAspectRatio 参数确保在缩放时保持视频的原始宽高比。
        这样可以防止视频被拉伸或压缩，保持正确的显示比例。
        """
        self.graphicsView.fitInView(self.videoItem, Qt.KeepAspectRatio)
    def on_subtitle_changed(self, new_srt):
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

    @property
    def player(self):

        return self.playBar.player
