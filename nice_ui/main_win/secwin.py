import copy
import os
from typing import List, Optional, Dict, Any

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QMessageBox

from nice_ui.configure.signal import data_bridge
from agent import translate_api_name
from nice_ui.configure import config
from nice_ui.configure.setting_cache import save_setting
from nice_ui.task import WORK_TYPE
from nice_ui.task.main_worker import QueueConsumer, Worker
from nice_ui.util import tools
from nice_ui.util.code_tools import language_code
from nice_ui.util.tools import start_tools
from nice_ui.services.service_provider import ServiceProvider
from utils import logger
from videotrans import translator

# 常量定义
DEFAULT_PROGRESS_RANGE = (0, 100)
PROGRESS_BAR_HEIGHT = 35


class ThreadManager:
    """
    线程管理器，负责创建和管理工作线程和消费线程
    """

    def __init__(self):
        self.queue_consumer: Optional[QueueConsumer] = None
        self.queue_consumer_thread: Optional[QThread] = None
        self.worker: Optional[Worker] = None
        self.worker_thread: Optional[QThread] = None
        self.data_bridge = data_bridge

    def create_worker_thread(self, data_copy: List[str], work_type: WORK_TYPE):
        """
        创建工作线程
        """
        self.worker_thread = QThread()
        self.worker = Worker(data_copy)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(lambda: self.worker.do_work(work_type))
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.error.connect(self.handle_error)
        self.worker.queue_ready.connect(self.start_queue_consumer)
        self.worker_thread.start()

        logger.debug("工作线程已启动")

    def start_queue_consumer(self):
        """
        启动队列消费线程
        """
        logger.debug(f"检查消费状态: {config.is_consuming}")
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
        """
        处理线程错误
        """
        logger.error(f"线程错误: {error_msg}")


class SecWindow:
    """
    主窗口的辅助类，负责处理各种功能逻辑
    """

    def __init__(self, main=None):
        self.main = main
        self.usetype: Optional[str] = None
        self.data_bridge = data_bridge
        self.thread_manager = ThreadManager()
        self.tools = start_tools

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
        """
        检查ASR任务并启动处理
        """
        config.params["only_video"] = False

        # 检查是否有视频文件
        if len(config.queue_asr) < 1:
            QMessageBox.critical(
                self.main,
                config.transobj["anerror"],
                config.transobj["bukedoubucunzai"],
            )
            return False

        config.params["only_video"] = True
        language_name = config.params["source_language"]

        # 检查模型信息
        if not self._check_source_model():
            return False

        # 如果需要翻译，获取翻译设置
        translate_status = config.params["translate_status"]
        if translate_status:
            self.get_trans_setting(language_name)

        # 保存设置
        self._save_current_settings()

        # 创建工作队列并启动处理
        queue_mp4_copy = copy.deepcopy(config.queue_asr)
        work_type = WORK_TYPE.ASR_TRANS if translate_status else WORK_TYPE.ASR
        self.add_queue_thread(queue_mp4_copy, work_type)
        self.update_status(work_type)

        return True

    def _check_source_model(self) -> bool:
        """
        检查源模型是否可用
        """
        source_model_info = self.tools.match_source_model(
            self.main.source_model.currentText()
        )
        logger.debug(f"==========source_model_info:{source_model_info}")

        model_name = source_model_info["model_name"]
        config.params["source_module_key"] = self.main.source_model.currentText()

        if self.tools.ask_model_folder(model_name):
            config.params["source_module_name"] = model_name
            config.params["source_module_status"] = source_model_info["status"]
            logger.debug(config.params["source_module_status"])
            return True
        else:
            QMessageBox.critical(
                self.main,
                "错误",
                "模型未下载，请在设置界面下载模型。"
            )
            return False

    def _save_current_settings(self):
        """
        保存当前设置
        """

        save_setting(self.main.settings)

        logger.debug("====config.settings====")
        logger.debug(config.settings)
        logger.debug("====config.params====")
        logger.debug(config.params)

    def check_translate(self) -> bool:
        """
        检查翻译任务并启动处理
        """
        # 获取源语言
        language_name = self.main.source_language_combo.currentText()
        logger.debug(f"==========language_name:{language_name}")
        config.params["source_language"] = language_name
        is_task = False
        # 获取翻译设置
        self.get_trans_setting(language_name)

        # 检查是否有待翻译文件
        if len(config.queue_trans) < 1:
            QMessageBox.critical(
                self.main,
                config.transobj["anerror"],
                config.transobj["bukedoubucunzai"],
            )
            return is_task
        is_task = self._check_auth_and_balance()
        # 保存设置
        if is_task:
            self._save_current_settings()

            # 创建工作队列并启动处理
            queue_srt_copy = copy.deepcopy(config.queue_trans)
            self.add_queue_thread(queue_srt_copy, WORK_TYPE.TRANS)
        self.update_status(WORK_TYPE.TRANS)
        return is_task

    def check_cloud_asr(self) -> bool:
        """
        云ASR引擎检查

        Returns:
            bool: 检查结果，True表示可以继续，False表示需要停止
        """
        # 检查登录状态和代币余额

        is_task = self._check_auth_and_balance()

        if is_task:
            # 保存设置
            self._save_current_settings()
            # 创建工作队列并启动处理
            queue_asr_copy = copy.deepcopy(config.queue_asr)
            logger.debug(f"add_queue_thread: {queue_asr_copy}")
            self.add_queue_thread(queue_asr_copy, WORK_TYPE.CLOUD_ASR)

        # 更新状态
        self.update_status(WORK_TYPE.CLOUD_ASR)
        return is_task

    def _check_auth_and_balance(self) -> bool:
        """
        检查用户登录状态和代币余额

        Returns:
            bool: 检查结果，True表示可以继续，False表示需要停止
        """
        # 获取服务
        service_provider = ServiceProvider()
        auth_service = service_provider.get_auth_service()
        token_service = service_provider.get_token_service()

        # 检查登录状态
        is_online, user_balance = auth_service.check_login_status()
        if not is_online:
            logger.warning("用户未登录或登录已过期")
            return False

        logger.info("用户已登录，可以继续使用云引擎")

        # 计算任务所需代币
        task_amount = self._calculate_total_tokens()
        logger.info(f"任务总代币消耗: {task_amount}")

        # 检查代币是否足够
        if user_balance is not None:
            if token_service.is_balance_sufficient_with_value(task_amount, user_balance):
                logger.info("代币余额足够，可以继续任务")
                return True
            else:
                # 余额不足，弹出充值窗口
                logger.warning("代币余额不足，需要充值")
                return token_service.prompt_recharge_dialog(task_amount)

        return False

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
        """
        创建工作线程并添加任务到队列
        """
        logger.debug("创建工作线程")
        self.thread_manager.create_worker_thread(data_copy, work_type)

    def update_status(self, ty: WORK_TYPE):
        if ty in [WORK_TYPE.ASR, WORK_TYPE.ASR_TRANS, WORK_TYPE.CLOUD_ASR]:
            self.main.table.clear_table(self.main.media_table)
            config.queue_asr = []
        elif ty == WORK_TYPE.TRANS:
            self.main.table.clear_table(self.main.media_table)
            config.queue_trans = []
        else:
            logger.error(f'WORK_TYPE;{WORK_TYPE} 未匹配')

    def _calculate_total_tokens(self) -> int:
        # 计算任务所需总代币
        task_amount = 0
        # 遍历表格中的所有行，累加每个任务的代币消耗
        for row in range(self.main.media_table.rowCount()):
            if token_item := self.main.media_table.item(row, 2):
                try:
                    # 尝试将单个任务的代币消耗转换为整数并累加
                    task_token = int(token_item.text())
                    task_amount += task_token

                    # 获取文件路径
                    file_path_item = self.main.media_table.item(row, 4)
                    if file_path_item and file_path_item.text():
                        file_path = file_path_item.text()
                        # 使用TokenService存储代币消费量
                        token_service = ServiceProvider().get_token_service()
                        token_service.set_task_token_amount(file_path, task_token)
                        logger.info(f"保存任务代币消耗: {task_token}, 文件路径: {file_path}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"解析代币消耗失败: {str(e)}")
        return task_amount
