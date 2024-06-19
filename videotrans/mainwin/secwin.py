import json
import os
import re
import shutil
import threading
from PySide6 import QtCore
from PySide6.QtGui import QTextCursor, QDesktopServices
from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import QMessageBox, QFileDialog, QLabel, QPushButton, QHBoxLayout, QProgressBar
import warnings

from videotrans import configure
# from videotrans.task.job import start_thread
# from videotrans.util import tools
# from videotrans import translator
from videotrans.configure import config
from pathlib import Path


class SecWindow():
    # 各页面所需控件
    def __init__(self, main=None):
        self.main = main
        self.usetype = None

    def set_tiquzimu(self):
        self.main.action_tiquzimu.setChecked(True)
        self.main.app_mode = 'tiqu'  # todo 还不知道干嘛的
        self.main.show_tips.setText(config.transobj['tiquzimu'])
        self.main.startbtn.setText(config.transobj['kaishitiquhefanyi'])
        self.main.action_tiquzimu.setChecked(True)
        self.main.action_xinshoujandan.setChecked(False)
        self.main.action_biaozhun.setChecked(False)
        self.main.action_zimu_video.setChecked(False)
        self.main.action_zimu_peiyin.setChecked(False)

        self.hide_show_element(self.main.subtitle_layout, True)
        self.main.splitter.setSizes([self.main.width - 400, 400])
        # 选择视频
        self.hide_show_element(self.main.layout_source_mp4, True)
        # 保存目标
        self.hide_show_element(self.main.layout_target_dir, True)

        # 隐藏音量 音调变化
        self.hide_show_element(self.main.edge_volume_layout, False)

        # 翻译渠道
        self.hide_show_element(self.main.layout_translate_type, True)
        # 代理
        self.hide_show_element(self.main.layout_proxy, True)
        # 原始语言
        self.hide_show_element(self.main.layout_source_language, True)
        # 目标语言
        self.hide_show_element(self.main.layout_target_language, True)
        # tts类型
        self.hide_show_element(self.main.layout_tts_type, False)
        # 配音角色
        self.hide_show_element(self.main.layout_voice_role, False)

        # 试听按钮

        self.main.listen_btn.hide()
        # 语音模型
        self.hide_show_element(self.main.layout_whisper_model, True)
        # 字幕类型
        self.hide_show_element(self.main.layout_subtitle_type, False)

        # 配音语速
        self.hide_show_element(self.main.layout_voice_rate, False)

        # 配音自动加速
        # 视频自动降速
        self.main.is_separate.setDisabled(True)
        self.main.addbackbtn.setDisabled(True)
        self.main.only_video.setDisabled(True)
        self.main.back_audio.setReadOnly(True)
        self.main.auto_ajust.setDisabled(True)
        self.main.video_autorate.setDisabled(True)
        self.main.voice_autorate.setDisabled(True)
        self.main.append_video.setDisabled(True)

        self.main.append_video.hide()
        self.main.voice_autorate.hide()
        self.main.is_separate.hide()
        self.main.addbackbtn.hide()
        self.main.back_audio.hide()
        self.main.only_video.hide()
        self.main.auto_ajust.hide()
        self.main.video_autorate.hide()

        # cuda
        self.main.enable_cuda.show()

    def update_status(self, type):
        config.current_status = type
        self.main.continue_compos.hide()
        self.main.stop_djs.hide()
        if type != 'ing':
            # 结束或停止
            self.main.subtitle_area.setReadOnly(False)
            self.main.subtitle_area.clear()
            self.main.startbtn.setText(config.transobj[type])
            # 启用
            self.disabled_widget(False)
            for k, v in self.main.moshis.items():
                v.setDisabled(False)
            if type == 'end':
                # 成功完成
                self.main.source_mp4.setText(config.transobj["No select videos"])
            else:
                # 停止
                self.main.continue_compos.hide()
                self.main.target_dir.clear()
                self.main.source_mp4.setText(config.transobj["No select videos"] if len(
                    config.queue_mp4) < 1 else f'{len(config.queue_mp4)} videos')
                # 清理输入
            if self.main.task:
                self.main.task.requestInterruption()
                self.main.task.quit()
                self.main.task = None
            if self.main.app_mode == 'tiqu':
                self.set_tiquzimu()
            elif self.main.app_mode == 'hebing':
                self.set_zimu_video()
            elif self.main.app_mode == 'peiyin':
                self.set_zimu_peiyin()
        else:
            # 重设为开始状态
            self.disabled_widget(True)
            self.main.startbtn.setText(config.transobj["starting..."])

    def disabled_widget(self, type):
        # 开启执行后，禁用按钮，停止或结束后，启用按钮
        self.main.clear_cache.setDisabled(type)
        self.main.import_sub.setDisabled(type)
        self.main.btn_get_video.setDisabled(type)
        self.main.btn_save_dir.setDisabled(type)
        self.main.translate_type.setDisabled(type)
        self.main.proxy.setDisabled(type)
        self.main.source_language.setDisabled(type)
        self.main.target_language.setDisabled(type)
        self.main.tts_type.setDisabled(type)
        self.main.whisper_model.setDisabled(type)
        self.main.whisper_type.setDisabled(type)
        self.main.subtitle_type.setDisabled(type)
        self.main.enable_cuda.setDisabled(type)
        self.main.model_type.setDisabled(type)
        self.main.voice_autorate.setDisabled(type)
        self.main.video_autorate.setDisabled(type)
        self.main.append_video.setDisabled(type)
        self.main.voice_role.setDisabled(type)
        self.main.voice_rate.setDisabled(type)
        self.main.only_video.setDisabled(True if self.main.app_mode in ['tiqu', 'peiyin'] else type)
        self.main.is_separate.setDisabled(True if self.main.app_mode in ['tiqu', 'peiyin'] else type)
        self.main.addbackbtn.setDisabled(True if self.main.app_mode in ['tiqu', 'hebing'] else type)
        self.main.back_audio.setReadOnly(True if self.main.app_mode in ['tiqu', 'hebing'] else type)
        self.main.auto_ajust.setDisabled(True if self.main.app_mode in ['tiqu', 'hebing'] else type)

    def hide_show_element(self, wrap_layout, show_status: bool) -> None:
        """
        显示布局及其元素
        Args:
            wrap_layout: 元素
            show_status: True显示|False隐藏

        Returns:

        """

        def hide_recursive(layout, show_status):
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget():
                    if not show_status:
                        item.widget().hide()
                    else:
                        item.widget().show()
                elif item.layout():
                    hide_recursive(item.layout(), show_status)

        hide_recursive(wrap_layout, show_status)
