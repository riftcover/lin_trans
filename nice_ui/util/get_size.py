from PySide6.QtGui import QFontMetrics

from utils import logger


def get_font_size(weight):
    font = weight.font()
    font_hight = QFontMetrics(font).height()
    logger.debug(f" {weight.__class__.__name__}font_hight: {font_hight}")


def get_widget_size(widget):
    size = widget.sizeHint()
    logger.debug(f"{widget.__class__.__name__} sizeHint: {size}")
