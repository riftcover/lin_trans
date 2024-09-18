from PySide6.QtCore import Signal, QObject



class DataBridge(QObject):
    # 定义信号
    checkbox_b_state_changed = Signal(bool)
    update_table = Signal(object, int)  # 音视频转文本添加文件的信号，用来更新我的创作页列表
    whisper_working = Signal(str, int)
    whisper_finished = Signal(str)

    def __init__(self):
        super().__init__()
        self._checkbox_b_state = False

    @property
    def checkbox_b_state(self):
        return self._checkbox_b_state

    @checkbox_b_state.setter
    def checkbox_b_state(self, value):
        if self._checkbox_b_state != value:
            self._checkbox_b_state = value
            self.checkbox_b_state_changed.emit(value)

    def emit_update_table(self, obj_format):
        from nice_ui.ui.my_story import SrtEditDict
        assert isinstance(obj_format, SrtEditDict)
        self.update_table.emit(obj_format, 1)

    def emit_whisper_working(self, unid, progress: int):
        self.whisper_working.emit(unid, progress)

    def emit_whisper_finished(self, status: str):
        """
        Args:
            status: True 成功 False 失败
        """
        self.whisper_finished.emit(status)
