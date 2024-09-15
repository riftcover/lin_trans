from PySide6.QtWidgets import QPushButton, QLabel
from components import lin_resource_rc
from components import LinIcon

# 创建一个带图标的按钮
export_button = QPushButton(LinIcon.EXPORT.icon(32), "Export")

# 或者使用类方法
up_button = QPushButton(LinIcon.get_icon('UP', 24), "Up")

# 创建一个图标标签
icon_label = QLabel()
icon_label.setPixmap(LinIcon.DOWN.pixmap(48))

# 或者使用类方法
icon_label2 = QLabel()
icon_label2.setPixmap(LinIcon.get_pixmap('DOWN_SQUARE', 48))