from PySide6.QtCore import Signal, QObject


class DataBridge(QObject):
    # 定义信号
    checkbox_b_state_changed = Signal(bool)
    update_table = Signal(object, int)  # 音视频转文本添加文件的信号，用来更新我的创作页列表
    whisper_working = Signal(str, int)
    whisper_finished = Signal(str)
    asr_trans_job_asr_finished = Signal(str)
    update_balance = Signal(int)  # 更新余额信号
    update_history = Signal(list)  # 更新历史记录信号
    task_error = Signal(str, str)  # 任务错误信号：(任务ID, 错误信息)

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
        from nice_ui.util.tools import VideoFormatInfo
        assert isinstance(obj_format, VideoFormatInfo)
        self.update_table.emit(obj_format, 1)

    def emit_whisper_working(self, unid, progress: int):
        self.whisper_working.emit(unid, progress)

    def emit_whisper_finished(self, status: str):
        """
        Args:
            status: unid
        """
        self.whisper_finished.emit(status)

    def emit_asr_finished(self, status: str):
        """
        Args:
            status: unid
        """
        self.asr_trans_job_asr_finished.emit(status)

    def emit_update_balance(self, balance: int):
        """
        发出更新余额信号
        Args:
            balance: 新的余额值
        """
        self.update_balance.emit(balance)

    def emit_update_history(self, transactions: list):
        """
        发出更新历史记录信号
        Args:
            transactions: 新的交易记录列表
        """
        self.update_history.emit(transactions)

    def emit_task_error(self, task_id: str, error_message: str):
        """
        发出任务错误信号
        Args:
            task_id: 任务ID
            error_message: 错误信息
        """
        self.task_error.emit(task_id, error_message)
