import copy
import os
from enum import Enum
from typing import List, Optional

from PySide6.QtCore import QUrl, Qt, QThread
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QMessageBox, QFileDialog, QLabel, QHBoxLayout, QProgressBar, )

from agent import translate_api_name
from nice_ui.configure import config
from nice_ui.configure.setting_cache import save_setting
from nice_ui.task import WORK_TYPE
from nice_ui.task.main_worker import QueueConsumer, Worker
from nice_ui.util import tools
from nice_ui.util.code_tools import language_code
from nice_ui.util.tools import StartTools
from utils import logger
from videotrans import translator

start_tools = StartTools()
# 提取常量
DEFAULT_PROGRESS_RANGE = (0, 100)
PROGRESS_BAR_HEIGHT = 35


class ProgressBarStyle(Enum):
    DEFAULT = """
        QProgressBar {
            background-color: transparent;
            border: 1px solid #32414B;
            color: #fff;
            height: 35px;
            text-align: left;
            border-radius: 3px;                
        }
        QProgressBar::chunk {
            width: 8px;
            border-radius: 0;           
        }
    """


class ClickableProgressBar(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_dir: Optional[str] = None
        self.msg: Optional[str] = None
        self.parent = parent

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(PROGRESS_BAR_HEIGHT)
        self.progress_bar.setRange(*DEFAULT_PROGRESS_RANGE)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(ProgressBarStyle.DEFAULT.value)

        layout = QHBoxLayout(self)
        layout.addWidget(self.progress_bar)

    def setMsg(self, text: str):
        if text and config.defaulelang == "zh":
            text += "\n\n请尝试在文档站 pyvideotrans.com 搜索错误解决方案\n"
        self.msg = text

    def setText(self, text: str):
        if self.progress_bar:
            self.progress_bar.setFormat(f" {text}")

    def mousePressEvent(self, event):
        if self.target_dir and event.button() == Qt.LeftButton:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.target_dir))
        elif not self.target_dir and self.msg:
            QMessageBox.critical(self, config.transobj["anerror"], self.msg)


class SecWindow:
    def __init__(self, main=None):
        self.queue_consumer: Optional[QueueConsumer] = None
        self.queue_consumer_thread: Optional[QThread] = None
        self.worker: Optional[Worker] = None
        self.worker_thread: Optional[QThread] = None
        self.main = main
        self.usetype: Optional[str] = None
        self.data_bridge = config.data_bridge

    def is_separate_fun(self, state: bool):
        config.params["is_separate"] = state

    def check_cuda(self, state: bool):
        import torch

        res = state
        if state and not torch.cuda.is_available():
            QMessageBox.critical(
                self.main, config.transobj["anerror"], config.transobj["nocuda"]
            )
            self.main.enable_cuda.setChecked(False)
            self.main.enable_cuda.setDisabled(True)
            res = False
        config.params["cuda"] = res
        if res:
            os.environ["CUDA_OK"] = "yes"
        elif os.environ.get("CUDA_OK"):
            os.environ.pop("CUDA_OK")

    def voice_rate_changed(self, text: int):
        config.params["voice_rate"] = f"+{text}%" if text >= 0 else f"{text}%"

    def autorate_changed(self, state: bool, name: str):
        if name == "voice":
            config.params["voice_autorate"] = state
        elif name == "auto_ajust":
            config.params["auto_ajust"] = state
        elif name == "video":
            config.params["video_autorate"] = state
        elif name == "append_video":
            config.params["append_video"] = state

    def delete_process(self):
        for i in range(self.main.processlayout.count()):
            item = self.main.processlayout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        self.main.processbtns = {}

    def export_sub_fun(self):
        srttxt = self.main.subtitle_area.toPlainText().strip()
        if not srttxt:
            return

        dialog = QFileDialog()
        dialog.setWindowTitle(config.transobj["savesrtto"])
        dialog.setNameFilters(["subtitle files (*.srt)"])
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.exec_()
        if not dialog.selectedFiles():
            return

        path_to_file = dialog.selectedFiles()[0]
        ext = ".srt"
        if not path_to_file.endswith((".srt", ".txt")):
            path_to_file += ext

        with open(path_to_file, "w", encoding="utf-8") as file:
            file.write(srttxt)

    def open_url(self, title: str):
        import webbrowser

        url_map = {
            "blog": "https://juejin.cn/user/4441682704623992/columns",
            "ffmpeg": "https://www.ffmpeg.org/download.html",
            "git": "https://github.com/jianchang512/pyvideotrans",
            "issue": "https://github.com/jianchang512/pyvideotrans/issues",
            "discord": "https://discord.gg/y9gUweVCCJ",
            "models": "https://github.com/jianchang512/stt/releases/tag/0.0",
            "dll": "https://github.com/jianchang512/stt/releases/tag/v0.0.1",
            "gtrans": "https://www.pyvideotrans.com/15.html",
            "cuda": "https://www.pyvideotrans.com/gpu.html",
            "website": "https://pyvideotrans.com",
            "help": "https://pyvideotrans.com",
            "xinshou": "https://www.pyvideotrans.com/guide.html",
            "about": "https://github.com/jianchang512/pyvideotrans/blob/main/about.md",
            "download": "https://github.com/jianchang512/pyvideotrans/releases",
            "openvoice": "https://github.com/kungful/openvoice-api",
        }

        if title in url_map:
            webbrowser.open_new_tab(url_map[title])
        elif title == "online":
            QMessageBox.information(self.main, "免责声明", self.get_disclaimer_text())

    @staticmethod
    def get_disclaimer_text():
        return """
免责声明：

在您下载或使用 "pyVideoTrans视频翻译配音" 软件（以下简称"本软件"）前，请仔细阅读并充分理解本免责声明中的各项条款。

您的下载、安装或使用行为将被视为对本免责声明的接受，并同意按照本声明内容约束自己的行为。如果您不同意本声明的任何条款，请不要下载、安装或使用本软件。

本软件所有源码均在 https://github.com/jianchang512/pyvideotrans 上开放。

1. 本软件是由独立开发者使用开源语音识别模型并结合第三方翻译API和第三方配音API开发的免费工具，旨在提供视频翻译和配音功能。开发者保证在软件运行过程中不会获取或存储用户数据。

2. 本软件中集成的语音识别功能（openai和faster模式）完全在本地环境下运行，不涉及将任何数据发送到开发者的服务器。当使用第三方翻译API和配音API时，相关数据将由用户的计算机直接传输至第三方服务器，未经开发者服务器处理。本软件无需用户注册或登录，不收集或存储任何个人信息。

3. 本软件纯属个人爱好项目，开发者无营利目的，未制定任何盈利计划，并不提供付费技术支持或其他付费服务。

4. 本软件不提供视频内容转移的功能，也不鼓励或支持任何形式的视频内容搬运行为。本软件仅旨在降低观赏外语视频时的语言障碍。

5. 用户在使用本软件时，须自觉遵守当地法律以及中华人民共和国的法律法规，敬重并维护他人版权和知识产权。

6. 用户因违反法律法规或侵犯他人权利而造成的任何后果，由用户本人承担，本软件开发者不承担任何连带责任。

7. 鉴于开发者从本软件中未获利，对于本软件的使用引发的任何问题或损失，开发者不负责任。

8. 本软件采用GPL-v3开源协议。任何基于本软件的二次开发或分支版本，需遵循GPL-v3协议规定，遵守相应义务和约束。

本软件的所有解释权均属于开发者。谨请用户在理解、同意、遵守本免责声明的前提下使用本软件。                
        """

    def set_djs_timeout(self):
        config.task_countdown = 0
        self.main.continue_compos.setText(config.transobj["jixuzhong"])
        self.main.continue_compos.setDisabled(True)
        self.main.stop_djs.hide()
        if self.main.shitingobj:
            self.main.shitingobj.stop = True

    def reset_timeid(self):
        self.main.stop_djs.hide()
        config.task_countdown = 86400
        self.main.continue_compos.setDisabled(False)
        self.main.continue_compos.setText(config.transobj["nextstep"])

    def check_whisper_type(self, index: int):
        whisper_types = ["all", "split", "avg"]
        if 0 <= index < len(whisper_types):
            config.params["whisper_type"] = whisper_types[index]

    def show_listen_btn(self, role: str):
        config.params["voice_role"] = role
        disable_condition = role == "No" or (
            config.params["tts_type"] == "clone-voice"
            and config.params["voice_role"] == "clone"
        )
        self.main.listen_btn.setDisabled(disable_condition)
        if not disable_condition:
            self.main.listen_btn.show()

    def set_voice_role(self, t: str):
        role = self.main.voice_role.currentText()
        code = translator.get_code(show_text=t)

        if code and code != "-":
            if config.params["tts_type"] == "GPT-SoVITS" and code[:2] not in [
                "zh",
                "ja",
                "en",
            ]:
                config.params["tts_type"] = "edgeTTS"
                self.main.tts_type.setCurrentText("edgeTTS")
                return QMessageBox.critical(
                    self.main,
                    config.transobj["anerror"],
                    config.transobj["nogptsovitslanguage"],
                )

            if config.params["tts_type"] == "ChatTTS" and code[:2] not in ["zh", "en"]:
                config.params["tts_type"] = "edgeTTS"
                self.main.tts_type.setCurrentText("edgeTTS")
                return QMessageBox.critical(
                    self.main,
                    config.transobj["anerror"],
                    config.transobj["onlycnanden"],
                )

        if config.params["tts_type"] not in ["edgeTTS", "AzureTTS"]:
            self.main.listen_btn.setDisabled(role == "No")
            if role != "No":
                self.main.listen_btn.show()
            return

        self.main.listen_btn.hide()
        show_rolelist = (
            tools.get_edge_rolelist()
            if config.params["tts_type"] == "edgeTTS"
            else tools.get_azure_rolelist()
        )

        if not show_rolelist:
            show_rolelist = tools.get_edge_rolelist()
        if not show_rolelist:
            self.main.translate_language.setCurrentText("-")
            return QMessageBox.critical(
                self.main, config.transobj["anerror"], config.transobj["waitrole"]
            )

        try:
            vt = code.split("-")[0]
            if vt not in show_rolelist or len(show_rolelist[vt]) < 2:
                self.main.translate_language.setCurrentText("-")
                return QMessageBox.critical(
                    self.main, config.transobj["anerror"], config.transobj["waitrole"]
                )

            self.main.current_rolelist = show_rolelist[vt]
            self.main.voice_role.addItems(show_rolelist[vt])
        except:
            self.main.voice_role.addItems(["No"])

    def get_mp4(self):
        fnames, _ = QFileDialog.getOpenFileNames(
            self.main,
            config.transobj["selectmp4"],
            config.last_opendir,
            "Video files(*.mp4 *.avi *.mov *.mpg *.mkv)",
        )
        if not fnames:
            return

        fnames = [it.replace("\\", "/") for it in fnames]
        if fnames:
            self.main.source_mp4.setText(f"{len(fnames)} videos")
            config.last_opendir = os.path.dirname(fnames[0])
            self.main.settings.setValue("last_dir", config.last_opendir)
            config.queue_asr = fnames

    def get_background(self):
        fname, _ = QFileDialog.getOpenFileName(
            self.main,
            "Background music",
            config.last_opendir,
            "Audio files(*.mp3 *.wav *.flac)",
        )
        if fname:
            self.main.back_audio.setText(fname.replace("\\", "/"))

    def dont_translate(self) -> bool:
        if len(config.queue_asr) < 1:
            return True
        if (
            self.main.translate_language.currentText() == "-"
            or self.main.source_language.currentText() == "-"
        ):
            return True
        if (
            self.main.translate_language.currentText()
            == self.main.source_language.currentText()
        ):
            return True
        return bool(self.main.subtitle_area.toPlainText().strip())

    def check_asr(self) -> bool:
        # logger.debug(f"Initial target_dir: {config.params['target_dir']}")
        #
        # if not config.params['target_dir']:
        #     config.params['target_dir'] = config.root_path / "result"
        #     logger.warning(f"target_dir was empty, reset to: {config.params['target_dir']}")

        self.main.add_queue_mp4()
        config.params["only_video"] = False

        if len(config.queue_asr) < 1:
            QMessageBox.critical(
                self.main,
                config.transobj["anerror"],
                config.transobj["bukedoubucunzai"],
            )
            return False

        config.params["only_video"] = True

        language_name = self.main.source_language.currentText()
        logger.debug(f"==========language_name:{language_name}")
        config.params["source_language"] = language_name
        config.params["source_language_code"] = language_code(language_name)

        source_model_info = start_tools.match_source_model(
            self.main.source_model.currentText()
        )
        config.params["source_module_status"] = source_model_info["status"]
        logger.debug(config.params["source_module_status"])
        config.params["source_module_name"] = source_model_info["model_name"]

        translate_status = self.main.check_fanyi.isChecked()
        config.params["translate_status"] = translate_status

        if translate_status:
            self.get_trans_setting(language_name)

        save_setting(self.main.settings)

        logger.info(f"update later config.queue_mp4:{config.queue_asr}")
        logger.debug("====config.settings====")
        logger.debug(config.settings)
        logger.debug("====config.params====")
        logger.debug(config.params)
        logger.debug("add_queue_thread")
        queue_mp4_copy = copy.deepcopy(config.queue_asr)

        work_type = WORK_TYPE.ASR_TRANS if translate_status else WORK_TYPE.ASR
        self.add_queue_thread(queue_mp4_copy, work_type)
        self.update_status(work_type)

        return True

    def check_translate(self) -> bool:
        self.main.add_queue_srt()
        language_name = self.main.source_language_combo.currentText()
        logger.debug(f"==========language_name:{language_name}")
        config.params["source_language"] = language_name

        self.get_trans_setting(language_name)

        if len(config.queue_trans) < 1:
            QMessageBox.critical(
                self.main,
                config.transobj["anerror"],
                config.transobj["bukedoubucunzai"],
            )
            return False

        save_setting(self.main.settings)

        queue_srt_copy = copy.deepcopy(config.queue_trans)
        self.add_queue_thread(queue_srt_copy, WORK_TYPE.TRANS)

        self.update_status(WORK_TYPE.TRANS)
        return True

    def get_trans_setting(self, language_name: str):
        translate_language_name = self.main.translate_language_combo.currentText()
        logger.debug(f"==========translate_language_name:{translate_language_name}")
        config.params["target_language"] = translate_language_name

        translate_language_channel_name = self.main.translate_model.currentText()
        translate_language_key = next(
            (
                key
                for key, value in translate_api_name.items()
                if value == translate_language_channel_name
            ),
            config.params["translate_channel"],
        )
        logger.debug(f"==========translate_language_name:{translate_language_key}")
        config.params["translate_channel"] = translate_language_key

        prompt_name = self.main.ai_prompt.currentText()
        config.params["prompt_name"] = prompt_name
        if prompt_body := self.main.prompts_orm.query_data_by_name(prompt_name):
            config.params["prompt_text"] = prompt_body.prompt_content.format(
                translate_name=translate_language_name,
                source_language_name=language_name,
            )

    def add_queue_thread(self, data_copy: List[str], work_type: WORK_TYPE):
        self.worker_thread = QThread()
        self.worker = Worker(data_copy)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(lambda: self.worker.do_work(work_type))
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.error.connect(self.handle_error)
        logger.debug("通知消费线程")
        self.worker.queue_ready.connect(self.start_queue_consumer)
        self.worker_thread.start()

    def start_queue_consumer(self):
        logger.debug(f"检查config.is_consuming:{config.is_consuming}")
        if not config.is_consuming:
            logger.debug("开始消费队列")
            self.queue_consumer_thread = QThread()
            self.queue_consumer = QueueConsumer()
            self.queue_consumer.moveToThread(self.queue_consumer_thread)
            self.queue_consumer_thread.started.connect(
                self.queue_consumer.process_queue
            )
            self.queue_consumer.finished.connect(self.queue_consumer_thread.quit)
            self.queue_consumer.finished.connect(self.queue_consumer.deleteLater)
            self.queue_consumer_thread.finished.connect(
                self.queue_consumer_thread.deleteLater
            )
            self.queue_consumer.error.connect(self.handle_error)
            self.queue_consumer_thread.start()
        else:
            logger.debug("消费队列正在工作")

    @staticmethod
    def handle_error(error_msg: str):
        logger.error(f"Error: {error_msg}")

    def update_status(self, ty: WORK_TYPE):
        if ty in [WORK_TYPE.ASR, WORK_TYPE.ASR_TRANS]:
            self.main.table.clear_table(self.main.media_table)
            config.queue_asr = []
        elif ty == WORK_TYPE.TRANS:
            self.main.table.clear_table(self.main.media_table)
            config.queue_trans = []
