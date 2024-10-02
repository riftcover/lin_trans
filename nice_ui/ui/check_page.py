import torch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from vendor.qfluentwidgets import (InfoBar, InfoBarPosition, PrimaryPushButton, FluentIcon as FIF, CardWidget, IconWidget, BodyLabel, CaptionLabel, )


class CudaCheckPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # CUDA 支持检查卡片
        self.cuda_support_card = self.create_info_card(
            "CUDA 支持", "检查系统是否支持 CUDA", FIF.UP, self.check_cuda_support
        )
        layout.addWidget(self.cuda_support_card)

        # CUDA 安装检查卡片
        self.cuda_install_card = self.create_info_card(
            "CUDA 安装",
            "检查 CUDA 是否已正确安装",
            FIF.DOWNLOAD,
            self.check_cuda_install,
        )
        layout.addWidget(self.cuda_install_card)

    def create_info_card(self, title, description, icon, check_function):
        card = CardWidget(self)
        card_layout = QVBoxLayout(card)

        # 图标和标题
        title_layout = QHBoxLayout()
        icon_widget = IconWidget(icon, self)
        title_label = BodyLabel(title, self)
        title_layout.addWidget(icon_widget)
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        card_layout.addLayout(title_layout)

        # 描述
        description_label = CaptionLabel(description, self)
        card_layout.addWidget(description_label)

        # 检查按钮
        check_button = PrimaryPushButton("检查", self)
        check_button.clicked.connect(check_function)
        card_layout.addWidget(check_button, alignment=Qt.AlignRight)

        return card

    def check_cuda_support(self):
        if torch.cuda.is_available():
            self.show_info("CUDA 支持", "您的系统支持 CUDA", FIF.UP)
        else:
            self.show_info("CUDA 支持", "您的系统不支持 CUDA", FIF.DOWNLOAD)

    def check_cuda_install(self):
        if torch.cuda.is_available():
            cuda_version = torch.version.cuda
            self.show_info(
                "CUDA 安装", f"CUDA 已正确安装，版本为 {cuda_version}", InfoBar.SUCCESS
            )
        else:
            self.show_info("CUDA 安装", "CUDA 未安装或未正确配置", FIF.DOWN)

    def show_info(self, title, content, icon):
        (
            InfoBar.success(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
            if icon == FIF.UP
            else InfoBar.warning(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
        )