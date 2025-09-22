#!/usr/bin/env python
"""
加密凭证管理GUI工具

提供图形界面来管理阿里云凭证的加密和解密操作
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QGroupBox, QFormLayout, QMessageBox, QFileDialog,
    QTabWidget, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon



from crypto_utils import crypto_utils


class CryptoGUI(QMainWindow):
    """加密凭证管理GUI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("加密凭证管理工具")
        self.setGeometry(100, 100, 600, 500)
        
        # 设置窗口图标和样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
        """)

        # 初始化变量
        self.selected_file_path = None
        self.current_root_dir = None  # 当前使用的根目录

        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 凭证管理标签页
        credentials_tab = self.create_credentials_tab()
        tab_widget.addTab(credentials_tab, "凭证管理")
        
        # 文件操作标签页
        file_tab = self.create_file_tab()
        tab_widget.addTab(file_tab, "文件操作")

        # 通用加解密标签页
        crypto_tab = self.create_crypto_tab()
        tab_widget.addTab(crypto_tab, "通用加解密")

        # 状态栏
        self.statusBar().showMessage("就绪")
        
    def create_credentials_tab(self):
        """创建凭证管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 根目录配置组
        root_dir_group = QGroupBox("根目录配置")
        root_dir_layout = QFormLayout(root_dir_group)

        # 根目录输入框和浏览按钮
        browse_layout = QHBoxLayout()
        self.root_dir_input = QLineEdit()
        self.root_dir_input.setPlaceholderText("输入项目根目录路径")
        self.root_dir_input.textChanged.connect(self.on_root_dir_changed)
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_root_dir)
        browse_layout.addWidget(self.root_dir_input)
        browse_layout.addWidget(browse_button)
        root_dir_layout.addRow("项目根目录:", browse_layout)

        # 阿里云凭证组
        aliyun_group = QGroupBox("阿里云凭证配置")
        aliyun_layout = QFormLayout(aliyun_group)
        
        self.aki_input = QLineEdit()
        self.aki_input.setPlaceholderText("输入AccessKey ID")
        aliyun_layout.addRow("AccessKey ID:", self.aki_input)
        
        self.aks_input = QLineEdit()
        self.aks_input.setPlaceholderText("输入AccessKey Secret")
        aliyun_layout.addRow("AccessKey Secret:", self.aks_input)
        
        self.region_input = QLineEdit("cn-beijing")
        aliyun_layout.addRow("区域:", self.region_input)
        
        self.bucket_input = QLineEdit("asr-file-tth")
        aliyun_layout.addRow("存储桶:", self.bucket_input)
        
        # ASR配置组
        aliyun_asr_group = QGroupBox("阿里云ASR配置")
        aliyun_asr_layout = QFormLayout(aliyun_asr_group)
        
        self.asr_api_key_input = QLineEdit()
        self.asr_api_key_input.setPlaceholderText("可选，输入ASR API密钥")
        aliyun_asr_layout.addRow("ASR API密钥:", self.asr_api_key_input)
        
        self.asr_model_input = QLineEdit("paraformer-v2")
        aliyun_asr_layout.addRow("ASR模型:", self.asr_model_input)

        # GladiaASR配置组
        gladia_asr_group = QGroupBox("GladiaASR配置")
        gladia_asr_layout = QFormLayout(gladia_asr_group)

        self.gladia_api_key_input = QLineEdit()
        self.gladia_api_key_input.setPlaceholderText("输入Gladia API密钥")
        gladia_asr_layout.addRow("Gladia API密钥:", self.gladia_api_key_input)

        
        # 加密配置组
        crypto_group = QGroupBox("加密配置")
        crypto_layout = QFormLayout(crypto_group)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("linlin_pan4646606")
        crypto_layout.addRow("加密密码:", self.password_input)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("保存凭证")
        self.save_button.clicked.connect(self.save_credentials)
        button_layout.addWidget(self.save_button)
        
        self.load_button = QPushButton("加载凭证")
        self.load_button.clicked.connect(self.load_credentials)
        button_layout.addWidget(self.load_button)
        
        self.clear_button = QPushButton("清空表单")
        self.clear_button.setStyleSheet("QPushButton { background-color: #f44336; }")
        self.clear_button.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_button)
        
        # 添加到布局
        layout.addWidget(root_dir_group)
        layout.addWidget(aliyun_group)
        layout.addWidget(aliyun_asr_group)
        layout.addWidget(gladia_asr_group)
        layout.addWidget(crypto_group)
        layout.addLayout(button_layout)
        layout.addStretch()

        return widget
        
    def create_file_tab(self):
        """创建文件操作标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 文件路径组
        file_group = QGroupBox("文件操作")
        file_layout = QVBoxLayout(file_group)
        
        # 当前凭证文件路径显示
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("凭证文件路径:"))
        
        self.file_path_label = QLabel()
        self.file_path_label.setStyleSheet("QLabel { background-color: white; padding: 5px; border: 1px solid #ddd; }")
        self.update_file_path_display()
        path_layout.addWidget(self.file_path_label)
        
        file_layout.addLayout(path_layout)
        
        # 文件操作按钮
        file_button_layout = QHBoxLayout()
        
        self.check_file_button = QPushButton("检查文件状态")
        self.check_file_button.clicked.connect(self.check_file_status)
        file_button_layout.addWidget(self.check_file_button)
        
        self.backup_button = QPushButton("备份凭证文件")
        self.backup_button.clicked.connect(self.backup_credentials)
        file_button_layout.addWidget(self.backup_button)
        
        self.restore_button = QPushButton("恢复凭证文件")
        self.restore_button.clicked.connect(self.restore_credentials)
        file_button_layout.addWidget(self.restore_button)
        
        file_layout.addLayout(file_button_layout)
        
        # 信息显示区域
        info_group = QGroupBox("信息显示")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(200)
        info_layout.addWidget(self.info_text)
        
        layout.addWidget(file_group)
        layout.addWidget(info_group)
        layout.addStretch()
        
        return widget

    def on_root_dir_changed(self):
        """根目录输入框内容变化时的处理"""
        root_dir_text = self.root_dir_input.text().strip()
        if root_dir_text and Path(root_dir_text).exists():
            self.current_root_dir = Path(root_dir_text)
            self.update_file_path_display()

    def browse_root_dir(self):
        """浏览选择根目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择项目根目录",
            str(self.current_root_dir),
            QFileDialog.ShowDirsOnly
        )

        if dir_path:
            self.root_dir_input.setText(dir_path)
            self.current_root_dir = Path(dir_path)
            self.update_file_path_display()

    def update_file_path_display(self):
        """更新文件路径显示"""
        try:
            file_path = crypto_utils.get_credentials_file_path(self.current_root_dir)
            self.file_path_label.setText(str(file_path))
        except Exception as e:
            self.file_path_label.setText(f"获取路径失败: {str(e)}")
            
    def save_credentials(self):
        """保存凭证"""
        try:
            # 验证必填字段
            if not self.aki_input.text().strip():
                QMessageBox.warning(self, "警告", "AccessKey ID不能为空！")
                return
                
            if not self.aks_input.text().strip():
                QMessageBox.warning(self, "警告", "AccessKey Secret不能为空！")
                return
            
            # 初始化加密工具
            password = self.password_input.text().strip()
            if password:
                crypto_utils.initialize(password)
            else:
                crypto_utils.initialize()
            
            # 准备凭证数据
            credentials = {
                'ppl_sdk': {
                    'aki': self.aki_input.text().strip(),
                    'aks': self.aks_input.text().strip(),
                    'region': self.region_input.text().strip(),
                    'bucket': self.bucket_input.text().strip(),
                    'asr_api_key': self.asr_api_key_input.text().strip(),
                    'asr_model': self.asr_model_input.text().strip(),
                    'gladia_api_key': self.gladia_api_key_input.text().strip()
                }
            }
            
            # 获取凭证文件路径并保存
            credentials_file = crypto_utils.get_credentials_file_path(self.current_root_dir)
            crypto_utils.encrypt_to_file(credentials, credentials_file)
            
            self.statusBar().showMessage(f"凭证已成功保存到: {credentials_file}")
            QMessageBox.information(self, "成功", f"凭证已加密并保存到:\n{credentials_file}")
            
        except Exception as e:
            error_msg = f"保存凭证失败: {str(e)}"
            self.statusBar().showMessage(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            
    def load_credentials(self):
        """加载凭证"""
        try:
            # 初始化加密工具
            password = self.password_input.text().strip()
            if password:
                crypto_utils.initialize(password)
            else:
                crypto_utils.initialize()
            
            # 获取凭证文件路径
            credentials_file = crypto_utils.get_credentials_file_path(self.current_root_dir)
            
            if not credentials_file.exists():
                QMessageBox.warning(self, "警告", f"凭证文件不存在:\n{credentials_file}")
                return
            
            # 解密并加载凭证
            credentials = crypto_utils.decrypt_from_file(credentials_file)
            
            if 'ppl_sdk' in credentials:
                ppl_config = credentials['ppl_sdk']
                self.aki_input.setText(ppl_config.get('aki', ''))
                self.aks_input.setText(ppl_config.get('aks', ''))
                self.region_input.setText(ppl_config.get('region', 'cn-beijing'))
                self.bucket_input.setText(ppl_config.get('bucket', 'asr-file-tth'))
                self.asr_api_key_input.setText(ppl_config.get('asr_api_key', ''))
                self.asr_model_input.setText(ppl_config.get('asr_model', 'paraformer-v2'))
                self.gladia_api_key_input.setText(ppl_config.get('gladia_api_key', ''))
            
        except Exception as e:
            error_msg = f"加载凭证失败: {str(e)}"
            self.statusBar().showMessage(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            
    def clear_form(self):
        """清空表单"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有输入字段吗？", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.aki_input.clear()
            self.aks_input.clear()
            self.region_input.clear("cn-beijing")
            self.bucket_input.clear("asr-file-tth")
            self.gladia_api_key_input.clear()
            self.asr_model_input.clear("paraformer-v2")
            self.asr_api_key_input.clear()
            self.gladia_api_key_input.clear()
            self.password_input.clear()
            self.statusBar().showMessage("表单已清空")
            
    def check_file_status(self):
        """检查文件状态"""
        try:
            credentials_file = crypto_utils.get_credentials_file_path(self.current_root_dir)
            
            info_text = f"凭证文件路径: {credentials_file}\n"
            info_text += f"文件存在: {'是' if credentials_file.exists() else '否'}\n"
            
            if credentials_file.exists():
                file_size = credentials_file.stat().st_size
                info_text += f"文件大小: {file_size} 字节\n"
                
                # 尝试解密验证
                try:
                    crypto_utils.initialize()
                    credentials = crypto_utils.decrypt_from_file(credentials_file)
                    info_text += "文件状态: 可正常解密\n"
                    info_text += f"包含配置: {list(credentials.keys())}\n"
                except Exception as decrypt_error:
                    info_text += f"解密失败: {str(decrypt_error)}\n"
            
            self.info_text.setText(info_text)
            
        except Exception as e:
            self.info_text.setText(f"检查文件状态失败: {str(e)}")
            
    def backup_credentials(self):
        """备份凭证文件"""
        try:
            credentials_file = crypto_utils.get_credentials_file_path(self.current_root_dir)
            
            if not credentials_file.exists():
                QMessageBox.warning(self, "警告", "凭证文件不存在，无法备份")
                return
            
            # 选择备份位置
            backup_path, _ = QFileDialog.getSaveFileName(
                self, "选择备份位置", 
                str(Path.home() / "aliyun_credentials_backup.enc"),
                "加密文件 (*.enc);;所有文件 (*)"
            )
            
            if backup_path:
                import shutil
                shutil.copy2(credentials_file, backup_path)
                QMessageBox.information(self, "成功", f"凭证文件已备份到:\n{backup_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"备份失败: {str(e)}")
            
    def restore_credentials(self):
        """恢复凭证文件"""
        try:
            # 选择要恢复的文件
            backup_path, _ = QFileDialog.getOpenFileName(
                self, "选择要恢复的凭证文件",
                str(Path.home()),
                "加密文件 (*.enc);;所有文件 (*)"
            )
            
            if backup_path:
                credentials_file = crypto_utils.get_credentials_file_path(self.current_root_dir)
                
                # 确认覆盖
                if credentials_file.exists():
                    reply = QMessageBox.question(
                        self, "确认", 
                        "当前凭证文件将被覆盖，确定继续吗？",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return
                
                import shutil
                shutil.copy2(backup_path, credentials_file)
                QMessageBox.information(self, "成功", "凭证文件已成功恢复")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"恢复失败: {str(e)}")

    def encrypt_text(self):
        """加密文本"""
        try:
            plain_text = self.plain_text_input.toPlainText().strip()
            if not plain_text:
                QMessageBox.warning(self, "警告", "请输入要加密的文本！")
                return

            # 初始化加密工具
            password = self.crypto_password_input.text().strip()
            if password:
                crypto_utils.initialize(password)
            else:
                crypto_utils.initialize()

            # 加密文本
            encrypted_data = crypto_utils.encrypt(plain_text)

            # 将二进制数据转换为base64字符串显示
            import base64
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')

            self.crypto_result_text.setText(encrypted_b64)
            self.statusBar().showMessage("文本加密成功")

        except Exception as e:
            error_msg = f"加密失败: {str(e)}"
            self.statusBar().showMessage(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def decrypt_text(self):
        """解密文本"""
        try:
            encrypted_text = self.plain_text_input.toPlainText().strip()
            if not encrypted_text:
                QMessageBox.warning(self, "警告", "请输入要解密的文本！")
                return

            # 初始化加密工具
            password = self.crypto_password_input.text().strip()
            if password:
                crypto_utils.initialize(password)
            else:
                crypto_utils.initialize()

            # 将base64字符串转换为二进制数据
            import base64
            try:
                encrypted_data = base64.b64decode(encrypted_text.encode('utf-8'))
            except Exception:
                QMessageBox.warning(self, "警告", "输入的不是有效的base64编码文本！")
                return

            # 解密文本
            decrypted_data = crypto_utils.decrypt(encrypted_data)

            # 显示解密结果
            if isinstance(decrypted_data, dict):
                import json
                result_text = json.dumps(decrypted_data, indent=2, ensure_ascii=False)
            else:
                result_text = str(decrypted_data)

            self.crypto_result_text.setText(result_text)
            self.statusBar().showMessage("文本解密成功")

        except Exception as e:
            error_msg = f"解密失败: {str(e)}"
            self.statusBar().showMessage(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def clear_text_areas(self):
        """清空文本区域"""
        self.plain_text_input.clear()
        self.crypto_result_text.clear()
        self.statusBar().showMessage("文本区域已清空")

    def copy_result(self):
        """复制结果到剪贴板"""
        result_text = self.crypto_result_text.toPlainText()
        if result_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(result_text)
            self.statusBar().showMessage("结果已复制到剪贴板")
        else:
            QMessageBox.warning(self, "警告", "没有可复制的内容！")

    def save_result_to_file(self):
        """保存结果到文件"""
        result_text = self.crypto_result_text.toPlainText()
        if not result_text:
            QMessageBox.warning(self, "警告", "没有可保存的内容！")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存结果",
                str(Path.home() / "crypto_result.txt"),
                "文本文件 (*.txt);;所有文件 (*)"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result_text)
                QMessageBox.information(self, "成功", f"结果已保存到:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def select_file_for_crypto(self):
        """选择要加解密的文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件",
            str(Path.home()),
            "所有文件 (*)"
        )

        if file_path:
            self.selected_file_path = file_path
            self.selected_file_label.setText(Path(file_path).name)
        else:
            self.selected_file_path = None
            self.selected_file_label.setText("未选择文件")

    def encrypt_file(self):
        """加密文件"""
        if not hasattr(self, 'selected_file_path') or not self.selected_file_path:
            QMessageBox.warning(self, "警告", "请先选择要加密的文件！")
            return

        try:
            # 初始化加密工具
            password = self.crypto_password_input.text().strip()
            if password:
                crypto_utils.initialize(password)
            else:
                crypto_utils.initialize()

            # 读取文件内容
            input_path = Path(self.selected_file_path)
            with open(input_path, 'rb') as f:
                file_data = f.read()

            # 加密数据
            encrypted_data = crypto_utils.encrypt(file_data)

            # 选择保存位置
            output_path, _ = QFileDialog.getSaveFileName(
                self, "保存加密文件",
                str(input_path.parent / f"{input_path.stem}_encrypted.enc"),
                "加密文件 (*.enc);;所有文件 (*)"
            )

            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(encrypted_data)

                QMessageBox.information(self, "成功", f"文件已加密并保存到:\n{output_path}")
                self.statusBar().showMessage("文件加密成功")

        except Exception as e:
            error_msg = f"文件加密失败: {str(e)}"
            self.statusBar().showMessage(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def decrypt_file(self):
        """解密文件"""
        if not hasattr(self, 'selected_file_path') or not self.selected_file_path:
            QMessageBox.warning(self, "警告", "请先选择要解密的文件！")
            return

        try:
            # 初始化加密工具
            password = self.crypto_password_input.text().strip()
            if password:
                crypto_utils.initialize(password)
            else:
                crypto_utils.initialize()

            # 读取加密文件
            input_path = Path(self.selected_file_path)
            with open(input_path, 'rb') as f:
                encrypted_data = f.read()

            # 解密数据
            decrypted_data = crypto_utils.decrypt(encrypted_data)

            # 如果解密结果是字符串，转换为字节
            if isinstance(decrypted_data, str):
                decrypted_data = decrypted_data.encode('utf-8')
            elif isinstance(decrypted_data, dict):
                import json
                decrypted_data = json.dumps(decrypted_data, indent=2, ensure_ascii=False).encode('utf-8')

            # 选择保存位置
            default_name = input_path.stem
            if default_name.endswith('_encrypted'):
                default_name = default_name[:-10]  # 移除 '_encrypted' 后缀

            output_path, _ = QFileDialog.getSaveFileName(
                self, "保存解密文件",
                str(input_path.parent / f"{default_name}_decrypted.txt"),
                "文本文件 (*.txt);;所有文件 (*)"
            )

            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(decrypted_data)

                QMessageBox.information(self, "成功", f"文件已解密并保存到:\n{output_path}")
                self.statusBar().showMessage("文件解密成功")

        except Exception as e:
            error_msg = f"文件解密失败: {str(e)}"
            self.statusBar().showMessage(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def create_crypto_tab(self):
        """创建通用加解密标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 密码设置组
        password_group = QGroupBox("密码设置")
        password_layout = QFormLayout(password_group)

        self.crypto_password_input = QLineEdit()
        self.crypto_password_input.setEchoMode(QLineEdit.Password)
        self.crypto_password_input.setPlaceholderText("留空使用默认密码")
        password_layout.addRow("加密密码:", self.crypto_password_input)


        # 文件加解密组
        file_crypto_group = QGroupBox("文件加解密")
        file_crypto_layout = QVBoxLayout(file_crypto_group)

        # 文件选择
        file_select_layout = QHBoxLayout()

        self.selected_file_label = QLabel("未选择文件")
        self.selected_file_label.setStyleSheet("QLabel { background-color: white; padding: 5px; border: 1px solid #ddd; }")
        file_select_layout.addWidget(self.selected_file_label)

        self.select_file_button = QPushButton("选择文件")
        self.select_file_button.clicked.connect(self.select_file_for_crypto)
        file_select_layout.addWidget(self.select_file_button)

        file_crypto_layout.addLayout(file_select_layout)

        # 文件操作按钮
        file_crypto_button_layout = QHBoxLayout()

        self.encrypt_file_button = QPushButton("加密文件")
        self.encrypt_file_button.clicked.connect(self.encrypt_file)
        file_crypto_button_layout.addWidget(self.encrypt_file_button)

        self.decrypt_file_button = QPushButton("解密文件")
        self.decrypt_file_button.clicked.connect(self.decrypt_file)
        file_crypto_button_layout.addWidget(self.decrypt_file_button)

        file_crypto_layout.addLayout(file_crypto_button_layout)

        # 添加到主布局
        layout.addWidget(password_group)
        layout.addWidget(file_crypto_group)
        layout.addStretch()

        return widget


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("加密凭证管理工具")
    app.setApplicationVersion("1.0.0")
    
    # 设置应用程序图标（如果有的话）
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = CryptoGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
