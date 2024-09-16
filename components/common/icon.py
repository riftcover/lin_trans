from enum import Enum

from PySide6.QtGui import QIcon


class LinIcon(Enum):
    """ Fluent icon """

    EXPORT = 'PhExport'

    def path(self):
        return f':/icon/assets/{self.value}.svg'

    def icon(self):
        return QIcon(self.path())

    def __call__(self):
        # 使得 LinIcon 实例在被调用时直接返回 QIcon 对象
        return self.icon()
