import copy
import os
from typing import List, Optional

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (QMessageBox, )

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



class SecWindow:
    def __init__(self, main=None):
        self.queue_consumer: Optional[QueueConsumer] = None
        self.queue_consumer_thread: Optional[QThread] = None
        self.worker: Optional[Worker] = None
        self.worker_thread: Optional[QThread] = None
        self.main = main
        self.usetype: Optional[str] = None
        self.data_bridge = config.data_bridge

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


    def check_asr(self) -> bool:
        # logger.debug(f"Initial target_dir: {config.params['target_dir']}")
        #
        # if not config.params['target_dir']:
        #     config.params['target_dir'] = config.root_path / "result"
        #     logger.warning(f"target_dir was empty, reset to: {config.params['target_dir']}")

        self.main.add_queue_mp4()
        config.params["only_video"] = False

        # 判断是否有视频文件，如果没有，则提示错误信息
        # check if there is any video file, if not, show error message
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

        model_name = source_model_info["model_name"]

        if start_tools.ask_model_folder(model_name):
            config.params["source_module_name"] = model_name
            config.params["source_module_status"] = source_model_info["status"]
            logger.debug(config.params["source_module_status"])
        else:
            QMessageBox.critical(
                self.main,
                "错误",
                "模型未下载，请在设置界面下载模型。"
            )
            return False


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
