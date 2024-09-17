import sys
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QComboBox,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QImage, QPixmap


class VideoPlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video/Audio Player")
        self.resize(800, 600)

        # 创建音频输出
        self.audio_output = QAudioOutput()

        # 创建媒体播放器和视频组件
        self.media_player = QMediaPlayer()
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)

        # 创建控制组件
        self.play_button = QPushButton("Play")
        self.progress_slider = QSlider(Qt.Horizontal)
        self.time_label = QLabel("00:00 / 00:00")
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.original_button = QPushButton("原始")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.fullscreen_button = QPushButton("全屏")

        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.video_widget)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.progress_slider)
        controls_layout.addWidget(self.time_label)
        controls_layout.addWidget(self.speed_combo)
        controls_layout.addWidget(self.original_button)
        controls_layout.addWidget(self.volume_slider)
        controls_layout.addWidget(self.fullscreen_button)

        layout.addLayout(controls_layout)
        self.setLayout(layout)

        # 连接信号和槽
        self.play_button.clicked.connect(self.play_pause)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        self.speed_combo.currentTextChanged.connect(self.change_speed)
        self.original_button.clicked.connect(self.reset_to_original)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status_changed)

        # 设置定时器更新进度
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000)  # 每秒更新一次

        self.is_slider_pressed = False

    def handle_media_status_changed(self, status):
        if status == QMediaPlayer.LoadedMedia:
            # 媒体加载完成后，设置到第一帧并暂停
            self.media_player.setPosition(0)
            self.media_player.pause()
            # 更新进度条和时间标签
            self.update_progress()

    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_button.setText("Play")
        else:
            self.media_player.play()
            self.play_button.setText("Pause")

    def slider_pressed(self):
        self.is_slider_pressed = True
        self.media_player.pause()

    def set_position(self, position):
        self.media_player.setPosition(position)
        self.update_progress()

    def slider_released(self):
        self.is_slider_pressed = False
        if self.play_button.text() == "Pause":
            self.media_player.play()

    def change_speed(self, speed):
        speed_value = float(speed[:-1])
        self.media_player.setPlaybackRate(speed_value)

    def reset_to_original(self):
        self.speed_combo.setCurrentText("1.0x")
        self.media_player.setPlaybackRate(1.0)

    def change_volume(self, volume):
        self.audio_output.setVolume(volume / 100.0)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def update_progress(self):
        if not self.is_slider_pressed:
            duration = self.media_player.duration()
            position = self.media_player.position()
            self.progress_slider.setRange(0, duration)
            self.progress_slider.setValue(position)
            self.time_label.setText(
                f"{self.format_time(position)} / {self.format_time(duration)}"
            )

    def format_time(self, milliseconds):
        seconds = milliseconds // 1000
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def set_media_source(self, file_path):
        self.media_player.setSource(QUrl.fromLocalFile(file_path))


# 使用示例
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     player = VideoPlayerWidget()
#     player.set_media_source('/Users/locodol/my_own/code/lin_trans/result/tt1/vv2.mp4')  # 可以是视频或音频文件
#     player.show()
#     sys.exit(app.exec())
