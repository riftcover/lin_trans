# coding:utf-8
from PySide6.QtCore import Qt, Signal, QUrl, QSizeF, QTimer, QEvent
from PySide6.QtGui import QPainter
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import QWidget, QGraphicsView, QVBoxLayout, QGraphicsScene

from ..common.style_sheet import FluentStyleSheet
from .media_play_bar import StandardMediaPlayBar, SimpleMediaPlayBar


class GraphicsVideoItem(QGraphicsVideoItem):
    """ Graphics video item """

    def paint(self, painter: QPainter, option, widget):
        painter.setCompositionMode(QPainter.CompositionMode_Difference)
        super().paint(painter, option, widget)


class LinVideoWidget(QWidget):
    """ Video widget """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.graphicsView = QGraphicsView(self)
        self.videoItem = QGraphicsVideoItem()
        self.graphicsScene = QGraphicsScene(self)
        self.playBar = SimpleMediaPlayBar(self)

        self.graphicsView.setScene(self.graphicsScene)
        self.graphicsScene.addItem(self.videoItem)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        self.vBoxLayout.addWidget(self.graphicsView)
        self.vBoxLayout.addWidget(self.playBar)
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.player.setVideoOutput(self.videoItem)
        FluentStyleSheet.MEDIA_PLAYER.apply(self)




    def setVideo(self, url: QUrl):
        """ set the video to play """
        self.player.setSource(url)
        # self.fitInView()

    def event(self, event):
        if event.type() in [QEvent.TouchBegin, QEvent.TouchUpdate, QEvent.TouchEnd]:
            print(f"Touch event: {event.type()} at {event.pos()}")
        return super().event(event)

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
        self.videoItem.setSize(QSizeF(self.graphicsView.size()))
        # self.graphicsView.fitInView(self.videoItem, Qt.KeepAspectRatio)

    @property
    def player(self):

        return self.playBar.player