import copy
import json
import os
import warnings

from PySide6 import QtCore
from PySide6.QtCore import QUrl, Qt, QThread
from PySide6.QtGui import QTextCursor, QDesktopServices
from PySide6.QtWidgets import QMessageBox, QFileDialog, QLabel, QPushButton, QHBoxLayout, QProgressBar

from agent import translate_api_name
from nice_ui.task import WORK_TYPE
from nice_ui.task.main_worker import QueueConsumer
from nice_ui.ui.SingalBridge import DataBridge
from nice_ui.configure.setting_cache import save_setting
from nice_ui.util.code_tools import language_code

from nice_ui.task.main_worker import Worker
from nice_ui.util import tools
from videotrans import translator
from nice_ui.configure import config
from nice_ui.util.tools import StartTools

start_tools = StartTools()


class ClickableProgressBar(QLabel):
    def __init__(self, parent=None):
        super().__init__()
        self.target_dir = None
        self.msg = None
        self.parent = parent

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(35)
        self.progress_bar.setRange(0, 100)  # 设置进度范围
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: transparent;
                border:1px solid #32414B;
                color:#fff;
                height:35px;
                text-align:left;
                border-radius:3px;                
            }
            QProgressBar::chunk {
                width: 8px;
                border-radius:0;           
            }
        """)
        layout = QHBoxLayout(self)
        layout.addWidget(self.progress_bar)  # 将进度条添加到布局

    def setMsg(self, text):
        if text and config.defaulelang == 'zh':
            text += '\n\n请尝试在文档站 pyvideotrans.com 搜索错误解决方案\n'
        self.msg = text

    def setText(self, text):
        if self.progress_bar:
            self.progress_bar.setFormat(f' {text}')  # set text format

    def mousePressEvent(self, event):
        if self.target_dir and event.button() == Qt.LeftButton:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.target_dir))
        elif not self.target_dir and self.msg:
            QMessageBox.critical(self, config.transobj['anerror'], self.msg)


# primary ui


class SecWindow:
    def __init__(self, main=None):
        self.queue_consumer = None
        self.queue_consumer_thread = None
        self.worker = None
        self.worker_thread = None
        self.main = main
        self.usetype = None
        self.data_bridge = DataBridge()

    def is_separate_fun(self, state):
        config.params['is_separate'] = True if state else False

    def check_cuda(self, state):
        import torch
        res = state
        # 选中如果无效，则取消
        if state and not torch.cuda.is_available():
            QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj['nocuda'])
            self.main.enable_cuda.setChecked(False)
            self.main.enable_cuda.setDisabled(True)
            res = False
        config.params['cuda'] = res
        if res:
            os.environ['CUDA_OK'] = "yes"
        elif os.environ.get('CUDA_OK'):
            os.environ.pop('CUDA_OK')

    # 配音速度改变时，更改全局
    def voice_rate_changed(self, text):
        # text = str(text).replace('+', '').replace('%', '').strip()
        # text = 0 if not text else int(text)
        # text = f'+{text}%' if text >= 0 else f'{text}%'
        config.params['voice_rate'] = f'+{text}%' if text >= 0 else f'{text}%'

    def autorate_changed(self, state, name):
        if name == 'voice':
            config.params['voice_autorate'] = state
        elif name == 'auto_ajust':
            config.params['auto_ajust'] = state
        elif name == 'video':
            config.params['video_autorate'] = state
        elif name == 'append_video':
            config.params['append_video'] = state

    # 隐藏布局及其元素

    # 删除proce里的元素
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
        dialog.setWindowTitle(config.transobj['savesrtto'])
        dialog.setNameFilters(["subtitle files (*.srt)"])
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.exec_()
        if not dialog.selectedFiles():  # If the user closed the choice window without selecting anything.
            return
        else:
            path_to_file = dialog.selectedFiles()[0]
        ext = ".srt"
        if path_to_file.endswith('.srt') or path_to_file.endswith('.txt'):
            path_to_file = path_to_file[:-4] + ext
        else:
            path_to_file += ext
        with open(path_to_file, "w", encoding='utf-8') as file:
            file.write(srttxt)

    def open_url(self, title):
        import webbrowser
        if title == 'blog':
            webbrowser.open_new_tab("https://juejin.cn/user/4441682704623992/columns")
        elif title == 'ffmpeg':
            webbrowser.open_new_tab("https://www.ffmpeg.org/download.html")
        elif title == 'git':
            webbrowser.open_new_tab("https://github.com/jianchang512/pyvideotrans")
        elif title == 'issue':
            webbrowser.open_new_tab("https://github.com/jianchang512/pyvideotrans/issues")
        elif title == 'discord':
            webbrowser.open_new_tab("https://discord.gg/y9gUweVCCJ")
        elif title == 'models':
            webbrowser.open_new_tab("https://github.com/jianchang512/stt/releases/tag/0.0")
        elif title == 'dll':
            webbrowser.open_new_tab("https://github.com/jianchang512/stt/releases/tag/v0.0.1")
        elif title == 'gtrans':
            webbrowser.open_new_tab("https://www.pyvideotrans.com/15.html")
        elif title == 'cuda':
            webbrowser.open_new_tab("https://www.pyvideotrans.com/gpu.html")
        elif title in ('website', 'help'):
            webbrowser.open_new_tab("https://pyvideotrans.com")
        elif title == 'xinshou':
            webbrowser.open_new_tab("https://www.pyvideotrans.com/guide.html")
        elif title == "about":
            webbrowser.open_new_tab("https://github.com/jianchang512/pyvideotrans/blob/main/about.md")
        elif title == 'download':
            webbrowser.open_new_tab("https://github.com/jianchang512/pyvideotrans/releases")
        elif title == 'openvoice':
            webbrowser.open_new_tab("https://github.com/kungful/openvoice-api")

        elif title == 'online':
            QMessageBox.information(self.main, '免责声明', """
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
            """)

    # 工具箱

    # 将倒计时设为立即超时
    def set_djs_timeout(self):
        config.task_countdown = 0
        self.main.continue_compos.setText(config.transobj['jixuzhong'])
        self.main.continue_compos.setDisabled(True)
        self.main.stop_djs.hide()
        if self.main.shitingobj:
            self.main.shitingobj.stop = True

    # 手动点击停止自动合并倒计时
    def reset_timeid(self):
        self.main.stop_djs.hide()
        config.task_countdown = 86400
        self.main.continue_compos.setDisabled(False)
        self.main.continue_compos.setText(config.transobj['nextstep'])

    def check_whisper_type(self, index):
        if index == 0:
            config.params['whisper_type'] = 'all'
        elif index == 1:
            config.params['whisper_type'] = 'split'
        else:
            config.params['whisper_type'] = 'avg'

    def show_listen_btn(self, role):
        config.params["voice_role"] = role
        if role == 'No' or (config.params['tts_type'] == 'clone-voice' and config.params['voice_role'] == 'clone'):
            self.main.listen_btn.setDisabled(True)
            return
        self.main.listen_btn.show()
        self.main.listen_btn.setDisabled(False)

    # 目标语言改变时设置配音角色
    def set_voice_role(self, t):
        # todo: 目标语言改变时设置配音角色暂时未添加
        role = self.main.voice_role.currentText()
        # 如果tts类型是 openaiTTS，则角色不变
        # 是edgeTTS时需要改变
        code = translator.get_code(show_text=t)
        if code and code != '-' and config.params['tts_type'] == 'GPT-SoVITS' and code[:2] not in ['zh', 'ja', 'en']:
            # 除此指望不支持
            config.params['tts_type'] = 'edgeTTS'
            self.main.tts_type.setCurrentText('edgeTTS')
            return QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj['nogptsovitslanguage'])
        if code and code != '-' and config.params['tts_type'] == 'ChatTTS' and code[:2] not in ['zh', 'en']:
            # 除此指望不支持
            config.params['tts_type'] = 'edgeTTS'
            self.main.tts_type.setCurrentText('edgeTTS')
            return QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj['onlycnanden'])

        # 除 edgeTTS外，其他的角色不会随语言变化
        if config.params['tts_type'] not in ['edgeTTS', 'AzureTTS']:
            if role != 'No':
                self.main.listen_btn.show()
                self.main.listen_btn.setDisabled(False)
            else:
                self.main.listen_btn.setDisabled(True)
            return

        self.main.listen_btn.hide()
        # self.main.voice_role.clear()
        # 未设置目标语言，则清空 edgeTTS角色
        # if t == '-':
        #     self.main.voice_role.addItems(['No'])
        #     return
        show_rolelist = tools.get_edge_rolelist() if config.params['tts_type'] == 'edgeTTS' else tools.get_azure_rolelist()

        if not show_rolelist:
            show_rolelist = tools.get_edge_rolelist()
        if not show_rolelist:
            self.main.translate_language.setCurrentText('-')
            QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj['waitrole'])
            return
        try:
            vt = code.split('-')[0]
            if vt not in show_rolelist:
                self.main.voice_role.addItems(['No'])
                return
            if len(show_rolelist[vt]) < 2:
                self.main.translate_language.setCurrentText('-')
                QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj['waitrole'])
                return
            self.main.current_rolelist = show_rolelist[vt]
            self.main.voice_role.addItems(show_rolelist[vt])
        except:
            self.main.voice_role.addItems(['No'])

    # get video filter mp4
    def get_mp4(self):

        fnames, _ = QFileDialog.getOpenFileNames(self.main, config.transobj['selectmp4'], config.last_opendir, "Video files(*.mp4 *.avi *.mov *.mpg *.mkv)")
        if len(fnames) < 1:
            return
        for (i, it) in enumerate(fnames):
            fnames[i] = it.replace('\\', '/')

        if len(fnames) > 0:
            self.main.source_mp4.setText(f'{len(fnames)} videos')
            config.last_opendir = os.path.dirname(fnames[0])
            self.main.settings.setValue("last_dir", config.last_opendir)
            config.queue_asr = fnames

    # 导入背景声音
    def get_background(self):
        fname, _ = QFileDialog.getOpenFileName(self.main, 'Background music', config.last_opendir, "Audio files(*.mp3 *.wav *.flac)")
        if not fname:
            return
        fname = fname.replace('\\', '/')
        self.main.back_audio.setText(fname)

    # 从本地导入字幕文件
    def import_sub_fun(self):
        fname, _ = QFileDialog.getOpenFileName(self.main, config.transobj['selectmp4'], config.last_opendir, "Srt files(*.srt *.txt)")
        if fname:
            content = ""
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                with open(fname, 'r', encoding='gbk') as f:
                    content = f.read()
            finally:
                if content:
                    self.main.subtitle_area.clear()
                    self.main.subtitle_area.insertPlainText(content.strip())
                else:
                    return QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj['import src error'])


    # 添加进度条
    def add_process_btn(self):
        clickable_progress_bar = ClickableProgressBar(self)
        clickable_progress_bar.progress_bar.setValue(0)  # 设置当前进度值
        clickable_progress_bar.setText(config.transobj["waitforstart"])
        clickable_progress_bar.setMinimumSize(500, 50)
        # # 将按钮添加到布局中
        self.main.processlayout.addWidget(clickable_progress_bar)
        return clickable_progress_bar

    # 检测各个模式下参数是否设置正确
    def check_mode(self, *, txt=None):
        # 如果是 从字幕配音模式, 只需要字幕和目标语言，不需要翻译和视频
        if self.main.app_mode == 'peiyin':
            if not txt or config.params['voice_role'] == 'No' or config.params['target_language'] == '-':
                QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj['peiyinmoshisrt'])
                return False
            # 去掉选择视频，去掉原始语言
            config.params['source_mp4'] = ''
            config.params['source_language'] = '-'
            config.params['subtitle_type'] = 0
            config.params['whisper_model'] = 'tiny'
            config.params['whisper_type'] = 'all'
            config.params['is_separate'] = False
            config.params['video_autorate'] = False
            config.params['append_video'] = False
            return True
        # 如果是 合并模式,必须有字幕，有视频，有字幕嵌入类型，允许设置视频减速
        # 不需要翻译
        if self.main.app_mode == 'hebing':
            if len(config.queue_asr) < 1 or config.params['subtitle_type'] < 1 or not txt:
                QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj['hebingmoshisrt'])
                return False
            config.params['is_separate'] = False
            config.params['target_language'] = '-'
            config.params['source_language'] = '-'
            config.params['voice_role'] = 'No'
            config.params['voice_rate'] = '+0%'
            config.params['voice_autorate'] = False
            config.params['video_autorate'] = False
            config.params['append_video'] = False
            config.params['whisper_model'] = 'tiny'
            config.params['whisper_type'] = 'all'
            config.params['back_audio'] = ''
            return True
        if self.main.app_mode == 'tiqu':
            # 提取字幕模式，必须有视频、有原始语言，语音模型
            if len(config.queue_asr) < 1:
                QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj['selectvideodir'])
                return False

            config.params['is_separate'] = False
            config.params['subtitle_type'] = 0
            config.params['voice_role'] = 'No'
            config.params['voice_rate'] = '+0%'
            config.params['voice_autorate'] = False
            config.params['video_autorate'] = False
            config.params['append_video'] = False
            config.params['back_audio'] = ''
        if self.main.app_mode == 'biaozhun_jd':
            config.params['voice_autorate'] = True
            config.params['video_autorate'] = True
            config.params['append_video'] = True
            config.params['auto_ajust'] = True
            config.params['is_separate'] = False
            config.params['back_audio'] = ''

        return True

    #
    # 判断是否需要翻译
    # 0 peiyin模式无需翻译，heibng模式无需翻译
    # 1. 不存在视频，则是字幕创建配音模式，无需翻译
    # 2. 不存在目标语言，无需翻译
    # 3. 原语言和目标语言相同，不需要翻译
    # 4. 存在字幕，不需要翻译
    # 是否无需翻译，返回True=无需翻译,False=需要翻译
    def dont_translate(self):
        if len(config.queue_asr) < 1:
            return True
        if self.main.translate_language.currentText() == '-' or self.main.source_language.currentText() == '-':
            return True
        if self.main.translate_language.currentText() == self.main.source_language.currentText():
            return True
        return bool(self.main.subtitle_area.toPlainText().strip())


    # 检测开始状态并启动
    def check_start(self):

        # 加载数据
        self.main.add_queue_mp4()

        # 倒计时
        config.task_countdown = config.settings['countdown_sec']
        config.settings = config.parse_init()

        # 原始语言
        language_name = self.main.source_language.currentText()
        config.logger.debug(f'==========language_name:{language_name}')
        config.params['source_language'] = language_name
        config.params['source_language_code'] = language_code(language_name)
        # config.logger.debug(config.params['source_language'])

        # 语音模型
        # config.logger.debug(self.main.source_model.currentText())
        config.params['source_module_status'] = start_tools.match_source_model(self.main.source_model.currentText())['status']
        config.logger.debug(config.params['source_module_status'])
        config.params['source_module_name'] = start_tools.match_source_model(self.main.source_model.currentText())['model_name']

        # 综合判断
        if len(config.queue_asr) < 1:
            QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj['bukedoubucunzai'])
            return False

        # cuda检测
        if 100 < config.params["source_module_status"] < 200:
            import torch
            if not torch.cuda.is_available():
                QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj["nocuda"])
                return
            else:
                allow = True
                try:
                    from torch.backends import cudnn
                    if not cudnn.is_available() or not cudnn.is_acceptable(torch.tensor(1.).cuda()):
                        allow = False
                except Exception:
                    allow = False

                if not allow:
                    self.main.enable_cuda.setChecked(False)
                    config.params['cuda'] = False
                    return QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj["nocudnn"])

        # 是否翻译
        translate_status = self.main.check_fanyi.isChecked()
        config.params['translate_status']: bool = translate_status
        # 目标语言
        target_language = self.main.translate_language.currentText()
        config.params['target_language'] = target_language

        # 翻译渠道
        config.params['translate_type'] = self.main.translate_type.currentText()

        # 如果需要翻译，再判断是否符合翻译规则
        # if target_language:
        #     if not self.dont_translate():
        #         rs = translator.is_allow_translate(translate_type=config.params['translate_type'],
        #                                            show_target=config.params['target_language'])
        #         if rs is not True:
        #             # 不是True，有错误
        #             QMessageBox.critical(self.main, config.transobj['anerror'], rs)
        #             return False

        # 存在视频
        config.params['only_video'] = False
        config.params['clear_cache'] = False

        if len(config.queue_asr) > 0:
            config.params['only_video'] = True

        save_setting(self.main.settings)

        config.logger.info(f'update later config.queue_mp4:{config.queue_asr}')
        config.settings = config.parse_init()
        config.logger.debug("====config.settings====")
        config.logger.debug(config.settings)
        config.logger.debug("====config.params====")
        config.logger.debug(config.params)
        config.logger.debug("add_queue_thread")
        queue_mp4_copy = copy.deepcopy(config.queue_asr)
        self.add_queue_thread(queue_mp4_copy, 'asr')

        self.update_status('asr')

    def check_translate(self):
        self.main.add_queue_srt()
        # 原始语言
        language_name = self.main.source_language_combo.currentText()
        config.logger.debug(f'==========language_name:{language_name}')
        config.params['source_language'] = language_name

        #翻译语种
        translate_language_name = self.main.translate_language_combo.currentText()
        config.logger.debug(f'==========translate_language_name:{translate_language_name}')
        config.params['target_language'] = translate_language_name

        # 翻译渠道
        translate_language_key = config.params["translate_type"]
        translate_language_name = self.main.translate_model.currentText()
        for key, value in translate_api_name.items():
            if value == translate_language_name:
                translate_language_key = key
        config.logger.debug(f'==========translate_language_name:{translate_language_key}')
        config.params['translate_type'] = translate_language_key

        prompt_name = self.main.ai_prompt.currentText()
        config.params['prompt_name'] = prompt_name
        config.params['prompt_text'] = self.main.prompts_orm.query_data_by_name(prompt_name)

        if len(config.queue_trans) < 1:
            QMessageBox.critical(self.main, config.transobj['anerror'], config.transobj['bukedoubucunzai'])
            return False

        save_setting(self.main.settings)

        queue_srt_copy = copy.deepcopy(config.queue_trans)
        self.add_queue_thread(queue_srt_copy, 'trans')

        self.update_status('trans')

    def add_queue_thread(self, data_copy, work_type):
        # 添加需处理文件到队列的线程

        self.worker_thread = QThread()
        self.worker = Worker(data_copy)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(lambda:self.worker.do_work(work_type))
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.error.connect(self.handle_error)
        config.logger.debug('通知消费线程')
        self.worker.queue_ready.connect(self.start_queue_consumer)  # 连接新信号
        self.worker_thread.start()

    def start_queue_consumer(self):
        config.logger.debug(f'检查config.is_consuming:{config.is_consuming}')
        if not config.is_consuming:
            config.logger.debug('开始消费队列')
            self.queue_consumer_thread = QThread()
            self.queue_consumer = QueueConsumer()
            self.queue_consumer.moveToThread(self.queue_consumer_thread)
            self.queue_consumer_thread.started.connect(self.queue_consumer.process_queue)
            self.queue_consumer.finished.connect(self.queue_consumer_thread.quit)
            self.queue_consumer.finished.connect(self.queue_consumer.deleteLater)
            self.queue_consumer_thread.finished.connect(self.queue_consumer_thread.deleteLater)
            self.queue_consumer.error.connect(self.handle_error)
            self.queue_consumer_thread.start()
        else:
            config.logger.debug("消费队列正在工作")

    def handle_error(self, error_msg):
        config.logger.error(f"Error: {error_msg}")

    # 更新执行状态
    def update_status(self, ty: WORK_TYPE):
        # config.current_status = type
        # 将列表media_table中的内容清空,queue list清空
        if ty == 'asr':
            self.main.table.clear_table(self.main.media_table)
            config.queue_asr = []
        elif ty == 'trans':
            self.main.table.clear_table(self.main.media_table)
            config.queue_trans = []