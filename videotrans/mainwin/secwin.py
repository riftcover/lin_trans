import contextlib
import json
import os
import re
import subprocess
import warnings
from pathlib import Path

from PySide6 import QtCore
from PySide6.QtCore import QUrl, Qt, Slot, QThread
from PySide6.QtGui import QTextCursor, QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QMessageBox, QFileDialog, QLabel, QPushButton, QHBoxLayout, QProgressBar, \
    QTableWidgetItem, QTableWidget

from videotrans.configure.config import result_path
from videotrans.task.main_worker import QueueConsumer

warnings.filterwarnings('ignore')
from videotrans.task.main_worker import Worker
from videotrans.task.job import start_thread
from videotrans.util import tools
from videotrans import translator
from videotrans.configure import config
from videotrans.util.tools import StartTools
# from qfluentwidgets import PrimaryPushButton

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


class SecWindow():
    def __init__(self, main=None):
        self.main = main
        self.usetype = None

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
        show_rolelist = tools.get_edge_rolelist() if config.params[
                                                         'tts_type'] == 'edgeTTS' else tools.get_azure_rolelist()

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

        fnames, _ = QFileDialog.getOpenFileNames(self.main, config.transobj['selectmp4'], config.last_opendir,
                                                 "Video files(*.mp4 *.avi *.mov *.mpg *.mkv)")
        if len(fnames) < 1:
            return
        for (i, it) in enumerate(fnames):
            fnames[i] = it.replace('\\', '/')

        if len(fnames) > 0:
            self.main.source_mp4.setText(f'{len((fnames))} videos')
            config.last_opendir = os.path.dirname(fnames[0])
            self.main.settings.setValue("last_dir", config.last_opendir)
            config.queue_mp4 = fnames

    # 导入背景声音
    def get_background(self):
        fname, _ = QFileDialog.getOpenFileName(self.main, 'Background music', config.last_opendir,
                                               "Audio files(*.mp3 *.wav *.flac)")
        if not fname:
            return
        fname = fname.replace('\\', '/')
        self.main.back_audio.setText(fname)

    # 从本地导入字幕文件
    def import_sub_fun(self):
        fname, _ = QFileDialog.getOpenFileName(self.main, config.transobj['selectmp4'], config.last_opendir,
                                               "Srt files(*.srt *.txt)")
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
                    return QMessageBox.critical(self.main, config.transobj['anerror'],
                                                config.transobj['import src error'])

    # 保存目录
    def get_save_dir(self):
        # todo:修改为导出文件夹,需要在导出页添加按钮后调整
        dirname = QFileDialog.getExistingDirectory(self.main, config.transobj['selectsavedir'], config.last_opendir)
        dirname = dirname.replace('\\', '/')
        self.main.output_dir.setText(dirname)

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
            if len(config.queue_mp4) < 1 or config.params['subtitle_type'] < 1 or not txt:
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
            if len(config.queue_mp4) < 1:
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
        if self.main.app_mode in ['peiyin', 'hebing']:
            return True
        if len(config.queue_mp4) < 1:
            return True
        if self.main.translate_language.currentText() == '-' or self.main.source_language.currentText() == '-':
            return True
        if self.main.translate_language.currentText() == self.main.source_language.currentText():
            return True
        return bool(self.main.subtitle_area.toPlainText().strip())

    # def change_proxy(self, p):
    #     # 设置或删除代理
    #     config.proxy = p.strip()
    #     try:
    #         if not config.proxy:
    #             # 删除代理
    #             tools.set_proxy('del')
    #         self.main.settings.setValue('proxy', config.proxy)
    #     except Exception:
    #         pass

    # 检测开始状态并启动
    def check_start(self):
        proxy = self.main.proxy.text().strip().replace('：', ':')
        if proxy:
            if not re.match(r'^(http|sock)', proxy, re.I):
                proxy = f'http://{proxy}'
            if not re.match(r'^(http|sock)(s|5)?://(\d+\.){3}\d+:\d+', proxy, re.I):
                question = tools.show_popup(
                    '请确认代理地址是否正确？' if config.defaulelang == 'zh' else 'Please make sure the proxy address is correct', """你填写的网络代理地址似乎不正确
一般代理/vpn格式为 http://127.0.0.1:数字端口号
如果不知道什么是代理请勿随意填写
ChatGPT等api地址请填写在菜单-设置-对应配置内。
如果确认代理地址无误，请点击 Yes 继续执行""" if config.defaulelang == 'zh' else 'The network proxy address you fill in seems to be incorrect, the general proxy/vpn format is http://127.0.0.1:port, if you do not know what is the proxy please do not fill in arbitrarily, ChatGPT and other api address please fill in the menu - settings - corresponding configuration. If you confirm that the proxy address is correct, please click Yes to continue.')
                if question != QMessageBox.Yes:
                    self.update_status('stop')
                    return

        # 倒计时
        config.task_countdown = config.settings['countdown_sec']
        config.settings = config.parse_init()
        # 设置或删除代理
        config.proxy = proxy
        with contextlib.suppress(Exception):
            if config.proxy:
                # 设置代理
                tools.set_proxy(config.proxy)
            else:
                # 删除代理
                tools.set_proxy('del')
        # 原始语言
        config.params['source_language'] = self.main.source_language.currentText()
        # config.logger.debug(config.params['source_language'])

        # 语音模型
        # config.logger.debug(self.main.source_model.currentText())
        config.params['source_module_status'] = start_tools.match_source_model(self.main.source_model.currentText())['status']
        config.logger.debug(config.params['source_module_status'])
        config.params['source_module_name'] = start_tools.match_source_model(self.main.source_model.currentText())['model_name']


        # 综合判断
        if len(config.queue_mp4) < 1:
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
                    # config.params['cuda'] = False # todo 我没有cuda设置看是否需要
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
        if target_language:
            if not self.dont_translate():
                rs = translator.is_allow_translate(translate_type=config.params['translate_type'],
                                                   show_target=config.params['target_language'])
                if rs is not True:
                    # 不是True，有错误
                    QMessageBox.critical(self.main, config.transobj['anerror'], rs)
                    return False

        # 存在视频
        config.params['only_video'] = False
        config.params['clear_cache']=False



        if len(config.queue_mp4) > 0:
            config.params['only_video'] = True
            # start_thread(self.main)  # todo: 起线程


        self.main.save_setting()

        config.logger.info(f'update later config.queue_mp4:{config.queue_mp4}')


        config.settings = config.parse_init()
        # config.logger.info("====config.settings====")
        config.logger.info(config.settings)
        # config.logger.info("====config.params====")
        config.logger.info(config.params)
        config.logger.info("add_queue_thread")
        self.add_queue_thread()

        self.update_status('ing')


        # for k, v in self.main.moshis.items():
        #     if k != self.main.app_mode:
        #         v.setDisabled(True)

    def add_queue_thread(self):
        # 添加需处理文件到队列的线程

        self.worker_thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.do_work)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.error.connect(self.handle_error)
        self.worker.queue_ready.connect(self.start_queue_consumer)  # 连接新信号
        self.worker_thread.start()


    def start_queue_consumer(self):
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

    # 设置按钮上的日志信息
    def set_process_btn_text(self, text, btnkey="", type="logs"):
        if not btnkey or btnkey not in self.main.processbtns:
            return
        if not self.main.task:
            return
        if btnkey == 'srt2wav':
            if not (self.main.task and self.main.task.video):
                return
            if type == 'succeed':
                text, basename = text.split('##')
                self.main.processbtns[btnkey].setTarget(text)
                self.main.processbtns[btnkey].setCursor(Qt.PointingHandCursor)
                precent = 100
                text = f'{config.transobj["endandopen"].replace("..", "")} {text}'
            else:
                precent = self.main.task.video.precent
                text = f'{config.transobj["running"].replace("..", "")} [{round(precent, 1)}%] /  {config.transobj["endopendir"]} {text}'
            self.main.processbtns[btnkey].progress_bar.setValue(precent)
            self.main.processbtns[btnkey].setText(text)
            return
        precent = round(self.main.task.tasklist[
                            btnkey].precent if self.main.task.tasklist and btnkey in self.main.task.tasklist else 0, 1)
        if type == 'succeed' or precent >= 100.0:

            target = self.main.task.tasklist[btnkey].obj['output']
            basename = self.main.task.tasklist[btnkey].obj['raw_basename']

            self.main.processbtns[btnkey].setTarget(target)
            self.main.processbtns[btnkey].setCursor(Qt.PointingHandCursor)

            text = f'{config.transobj["endandopen"]} {basename}'
            self.main.processbtns[btnkey].setText(text)
            self.main.processbtns[btnkey].progress_bar.setValue(100)
            self.main.processbtns[btnkey].setToolTip(config.transobj['mubiao'])
        elif type == 'error' or type == 'stop':
            self.main.processbtns[btnkey].progress_bar.setStyleSheet('color:#ff0000')
            if type == 'error':
                self.main.processbtns[btnkey].setCursor(Qt.PointingHandCursor)
                self.main.processbtns[btnkey].setMsg(
                    text + f'\n\n{config.errorlist[btnkey] if btnkey in config.errorlist and config.errorlist[btnkey] != text else ""}'
                )
                self.main.processbtns[btnkey].setToolTip(
                    '点击查看详细报错' if config.defaulelang == 'zh' else 'Click to view the detailed error report')
                self.main.processbtns[btnkey].setText(text[:120])
            else:
                self.main.processbtns[btnkey].setToolTip('')
        elif btnkey in self.main.task.tasklist:
            jindu = f' {precent}% '
            self.main.processbtns[btnkey].progress_bar.setValue(int(self.main.task.tasklist[btnkey].precent))
            raw_name = self.main.task.tasklist[btnkey].obj['raw_basename']
            self.main.processbtns[btnkey].setToolTip(config.transobj["endopendir"])

            self.main.processbtns[btnkey].setText(
                f'{config.transobj["running"].replace("..", "")} [{jindu}] {raw_name} / {config.transobj["endopendir"]} {text}')

    # 更新执行状态
    def update_status(self, type):
        config.current_status = type
        # 当type为ing时将列表media_table中的内容清空,queue_mp4清空
        if type == 'ing':
            TableWindow().clearTable(self.main.media_table)
            config.queue_mp4 = []
            # QMessageBox.information(self.main, config.transobj['running'], config.transobj["Check the progress"])


    # 更新 UI
    def update_data(self, json_data):
        d = json.loads(json_data)
        if d['type'] == 'alert':
            QMessageBox.critical(self.main, config.transobj['anerror'], d['text'])
            return

        # 一行一行插入字幕到字幕编辑区
        elif d['type'] == 'set_start_btn':
            self.main.startbtn.setText(config.transobj["running"])
        elif d['type'] == "subtitle":
            self.main.subtitle_area.moveCursor(QTextCursor.End)
            self.main.subtitle_area.insertPlainText(d['text'])
        elif d['type'] == 'add_process':
            self.main.processbtns[d['btnkey']] = self.add_process_btn()
        elif d['type'] == 'rename':
            self.main.show_tips.setText(d['text'])
        elif d['type'] == 'set_target_dir':
            self.main.target_dir.setText(d['text'])
        elif d['type'] == "logs":
            self.set_process_btn_text(d['text'], btnkey=d['btnkey'])
        elif d['type'] == 'stop' or d['type'] == 'end' or d['type'] == 'error':
            if d['type'] == 'error':
                self.set_process_btn_text(d['text'], btnkey=d['btnkey'], type=d['type'])
            elif d['type'] == 'stop':
                # self.set_process_btn_text(config.transobj['stop'], d['btnkey'], d['type'])
                self.main.subtitle_area.clear()
            if d['type'] == 'stop' or d['type'] == 'end':
                self.update_status(d['type'])
                self.main.continue_compos.hide()
                self.main.target_dir.clear()
                self.main.stop_djs.hide()
                self.main.export_sub.setDisabled(False)
                self.main.set_line_role.setDisabled(False)
        elif d['type'] == 'succeed':
            # 本次任务结束
            self.set_process_btn_text(d['text'], btnkey=d['btnkey'], type='succeed')
        elif d['type'] == 'edit_subtitle':
            # 显示出合成按钮,等待编辑字幕,允许修改字幕
            self.main.subtitle_area.setReadOnly(False)
            self.main.subtitle_area.setFocus()
            self.main.continue_compos.show()
            self.main.continue_compos.setDisabled(False)
            self.main.continue_compos.setText(d['text'])
            self.main.stop_djs.show()
        elif d['type'] == 'disabled_edit':
            # 禁止修改字幕
            self.main.subtitle_area.setReadOnly(True)
            self.main.export_sub.setDisabled(True)
            self.main.set_line_role.setDisabled(True)
        elif d['type'] == 'allow_edit':
            # 允许修改字幕
            self.main.subtitle_area.setReadOnly(False)
            self.main.export_sub.setDisabled(False)
            self.main.set_line_role.setDisabled(False)
        elif d['type'] == 'replace_subtitle':
            # 完全替换字幕区
            self.main.subtitle_area.clear()
            self.main.subtitle_area.insertPlainText(d['text'])
        elif d['type'] == 'timeout_djs':
            self.main.stop_djs.hide()
            self.update_subtitle(step=d['text'], btnkey=d['btnkey'])
            self.main.continue_compos.setDisabled(True)
            self.main.subtitle_area.setReadOnly(True)
        elif d['type'] == 'show_djs':
            self.set_process_btn_text(d['text'], btnkey=d['btnkey'])
        elif d['type'] == 'check_soft_update':
            if not self.usetype:
                self.usetype = QPushButton()
                self.usetype.setStyleSheet('color:#ffff00;border:0')
                self.usetype.setCursor(QtCore.Qt.PointingHandCursor)
                self.usetype.clicked.connect(lambda: self.open_url('download'))
                self.main.container.addWidget(self.usetype)
            self.usetype.setText(d['text'])

        elif d['type'] == 'update_download' and self.main.youw is not None:
            self.main.youw.logs.setText(config.transobj['youtubehasdown'])
        elif d['type'] == 'youtube_error':
            self.main.youw.set.setText(config.transobj['start download'])
            QMessageBox.critical(self.main.youw, config.transobj['anerror'], d['text'][:900])

        elif d['type'] == 'youtube_ok':
            self.main.youw.set.setText(config.transobj['start download'])
            QMessageBox.information(self.main.youw, "OK", d['text'])
        elif d['type'] == 'open_toolbox':
            self.open_toolbox(0, True)
        elif d['type'] == 'set_clone_role' and config.params['tts_type'] == 'clone-voice':
            self.main.settings.setValue("clone_voicelist", ','.join(config.clone_voicelist))
            if config.current_status == 'ing':
                return
            current = self.main.voice_role.currentText()
            self.main.voice_role.clear()
            self.main.voice_role.addItems(config.clone_voicelist)
            self.main.voice_role.setCurrentText(current)
        elif d['type'] == 'win':
            # 小窗口背景音分离
            if self.main.sepw is not None:
                self.main.sepw.set.setText(d['text'])

    # update subtitle 手动 点解了 立即合成按钮，或者倒计时结束超时自动执行
    def update_subtitle(self, step="translate_start", btnkey=""):
        self.main.stop_djs.hide()
        self.main.continue_compos.setDisabled(True)
        # 如果当前是等待翻译阶段，则更新原语言字幕,然后清空字幕区
        txt = self.main.subtitle_area.toPlainText().strip()
        config.task_countdown = 0
        if not btnkey or not txt:
            return
        if btnkey == 'srt2wav':
            srtfile = self.main.task.video.init['target_sub']
            with open(srtfile, 'w', encoding='utf-8') as f:
                f.write(txt)
            return

        if not self.main.task.is_batch and btnkey in self.main.task.tasklist:
            if step == 'translate_start':
                srtfile = self.main.task.tasklist[btnkey].init['source_sub']
            else:
                srtfile = self.main.task.tasklist[btnkey].init['target_sub']
            # 不是批量才允许更新字幕
            with open(srtfile, 'w', encoding='utf-8') as f:
                f.write(txt)
        if step == 'translate_start':
            self.main.subtitle_area.clear()
        return True



class TableWindow(SecWindow):
    # 列表的操作
    @Slot()
    def select_files(self, ui_table: QTableWidget):
        # 选择文件
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_paths, _ = QFileDialog.getOpenFileNames(self.main, config.transobj['selectmp4'], config.last_opendir,
                                                     "Video files(*.mp4 *.avi *.mov *.mpg *.mkv)")

        if file_paths:
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                self.add_file_to_table(ui_table, file_name)
            config.last_opendir = os.path.dirname(file_paths[0])
            self.main.settings.setValue("last_dir", config.last_opendir)
            config.queue_mp4 = file_paths

    def add_file_to_table(self, ui_table: QTableWidget, file_name: str):
        # 添加文件到表格

        row_position = ui_table.rowCount()

        ui_table.insertRow(row_position)
        file_duration = "00:00:00"  # todo: 可以使用一个方法来获取实际时长
        # file_duration = self.get_video_duration(file_path)
        delete_button = QPushButton("删除")
        delete_button.setStyleSheet("background-color: red; color: white;")  # todo: 调整样式
        ui_table.setItem(row_position, 0, QTableWidgetItem(file_name))
        ui_table.setItem(row_position, 1, QTableWidgetItem(file_duration))
        ui_table.setItem(row_position, 2, QTableWidgetItem("未知"))
        ui_table.setCellWidget(row_position, 3, delete_button)

        delete_button.clicked.connect(lambda _, row=row_position: self.delete_file(ui_table, row))

    @Slot()
    def delete_file(self, ui_table: QTableWidget, row: int):
        # Confirm delete action

        ui_table.removeRow(row)
        # Update the delete buttons' connections
        self.update_delete_buttons(ui_table)

    def update_delete_buttons(self, ui_table: QTableWidget):
        for row in range(ui_table.rowCount()):
            delete_button = ui_table.cellWidget(row, 3)
            delete_button.clicked.disconnect()
            delete_button.clicked.connect(lambda _, r=row: self.delete_file(ui_table, r))

    def get_video_duration(self, file: Path):
        # Use ffprobe to get video duration
        cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{file}\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        duration_seconds = float(result.stdout.strip())
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def drag_enter_event(self, event: QDragEnterEvent):
        # 接受拖入
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def drop_event(self,ui_table: QTableWidget, event: QDropEvent):
        # 拖出
        file_urls = event.mimeData().urls()
        config.logger.info(f'file_urls: {file_urls}')
        file_paths = []
        if file_urls:
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                file_paths.append(file_path)
                config.logger.info(f'file_path: {file_path}')
                file_name = os.path.basename(file_path)
                config.logger.info(f'file_name: {file_name}')
                self.add_file_to_table(ui_table, file_name)
            config.queue_mp4 = file_paths
        event.accept()
        # ui_table.setText("\n".join(self.file_paths))

    def clearTable(self,ui_table: QTableWidget):
        # 清空表格
        ui_table.setRowCount(0)
