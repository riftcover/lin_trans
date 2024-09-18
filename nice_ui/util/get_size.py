from PySide6.QtGui import QFontMetrics

from nice_ui.configure.config import logger


def get_font_size(weight):
    font = weight.font()
    font_hight = QFontMetrics(font).height()
    logger.debug(f" {weight}font_hight: {font_hight}")


def get_widget_size(widget):
    size = widget.sizeHint()
    logger.debug(f"{widget} sizeHint: {size}")
