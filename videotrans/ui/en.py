# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'linlin.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication,QMetaObject,QRect, QSize,
                            Qt)
from PySide6.QtGui import (QAction)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMenu, QMenuBar, QPushButton, QSizePolicy, QStackedWidget, QStatusBar,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(930, 674)
        self.action = QAction(MainWindow)
        self.action.setObjectName(u"action")
        self.action_2 = QAction(MainWindow)
        self.action_2.setObjectName(u"action_2")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.listWidget = QListWidget(self.centralwidget)
        QListWidgetItem(self.listWidget)
        QListWidgetItem(self.listWidget)
        QListWidgetItem(self.listWidget)
        QListWidgetItem(self.listWidget)
        QListWidgetItem(self.listWidget)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setGeometry(QRect(0, 0, 90, 601))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setMaximumSize(QSize(90, 16777215))
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setGeometry(QRect(90, 0, 831, 601))
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.layoutWidget = QWidget(self.page)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(12, 16, 777, 578))
        self.verticalLayout_4 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.btn_get_video = QPushButton(self.layoutWidget)
        self.btn_get_video.setObjectName(u"btn_get_video")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_get_video.sizePolicy().hasHeightForWidth())
        self.btn_get_video.setSizePolicy(sizePolicy1)
        self.btn_get_video.setMinimumSize(QSize(300, 150))

        self.verticalLayout_4.addWidget(self.btn_get_video)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFormAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_2 = QLabel(self.layoutWidget)
        self.label_2.setObjectName(u"label_2")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy2)
        self.label_2.setMinimumSize(QSize(0, 35))

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.source_language = QComboBox(self.layoutWidget)
        self.source_language.setObjectName(u"source_language")
        sizePolicy1.setHeightForWidth(self.source_language.sizePolicy().hasHeightForWidth())
        self.source_language.setSizePolicy(sizePolicy1)
        self.source_language.setMinimumSize(QSize(0, 35))

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.source_language)

        self.horizontalLayout.addLayout(self.formLayout)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setFormAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_3 = QLabel(self.layoutWidget)
        self.label_3.setObjectName(u"label_3")
        sizePolicy2.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy2)
        self.label_3.setMinimumSize(QSize(0, 35))

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.source_model = QComboBox(self.layoutWidget)
        self.source_model.setObjectName(u"source_model")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.source_model.sizePolicy().hasHeightForWidth())
        self.source_model.setSizePolicy(sizePolicy3)
        self.source_model.setMinimumSize(QSize(0, 35))

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.source_model)

        self.horizontalLayout.addLayout(self.formLayout_2)

        self.check_fanyi = QCheckBox(self.layoutWidget)
        self.check_fanyi.setObjectName(u"check_fanyi")
        sizePolicy3.setHeightForWidth(self.check_fanyi.sizePolicy().hasHeightForWidth())
        self.check_fanyi.setSizePolicy(sizePolicy3)
        self.check_fanyi.setMinimumSize(QSize(0, 35))

        self.horizontalLayout.addWidget(self.check_fanyi)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setFormAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_8 = QLabel(self.layoutWidget)
        self.label_8.setObjectName(u"label_8")
        sizePolicy2.setHeightForWidth(self.label_8.sizePolicy().hasHeightForWidth())
        self.label_8.setSizePolicy(sizePolicy2)
        self.label_8.setMinimumSize(QSize(0, 35))

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_8)

        self.translate_type = QComboBox(self.layoutWidget)
        self.translate_type.setObjectName(u"translate_type")
        sizePolicy3.setHeightForWidth(self.translate_type.sizePolicy().hasHeightForWidth())
        self.translate_type.setSizePolicy(sizePolicy3)
        self.translate_type.setMinimumSize(QSize(0, 35))

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.translate_type)

        self.horizontalLayout.addLayout(self.formLayout_3)

        self.formLayout_4 = QFormLayout()
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.formLayout_4.setFormAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_4 = QLabel(self.layoutWidget)
        self.label_4.setObjectName(u"label_4")
        sizePolicy2.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy2)
        self.label_4.setMinimumSize(QSize(0, 35))

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_4)

        self.translate_language = QComboBox(self.layoutWidget)
        self.translate_language.setObjectName(u"translate_language")
        sizePolicy3.setHeightForWidth(self.translate_language.sizePolicy().hasHeightForWidth())
        self.translate_language.setSizePolicy(sizePolicy3)
        self.translate_language.setMinimumSize(QSize(0, 0))

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.translate_language)

        self.horizontalLayout.addLayout(self.formLayout_4)

        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(80, -1, 80, -1)
        self.media_table = QTableWidget(self.layoutWidget)
        if (self.media_table.columnCount() < 4):
            self.media_table.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.media_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.media_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.media_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.media_table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.media_table.setObjectName(u"media_table")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.media_table.sizePolicy().hasHeightForWidth())
        self.media_table.setSizePolicy(sizePolicy4)
        self.media_table.setMinimumSize(QSize(0, 300))

        self.verticalLayout.addWidget(self.media_table)

        self.verticalLayout_4.addLayout(self.verticalLayout)

        self.formLayout_5 = QFormLayout()
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.formLayout_5.setFormAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout_5.setContentsMargins(-1, -1, -1, 20)
        self.startbtn_1 = QPushButton(self.layoutWidget)
        self.startbtn_1.setObjectName(u"startbtn_1")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.startbtn_1.sizePolicy().hasHeightForWidth())
        self.startbtn_1.setSizePolicy(sizePolicy5)
        self.startbtn_1.setMinimumSize(QSize(200, 50))

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.startbtn_1)

        self.verticalLayout_4.addLayout(self.formLayout_5)

        self.stackedWidget.addWidget(self.page)

        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.layoutWidget1 = QWidget(self.page_2)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(12, 16, 678, 564))
        self.verticalLayout_5 = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.btn_get_srt = QPushButton(self.layoutWidget1)
        self.btn_get_srt.setObjectName(u"btn_get_srt")
        sizePolicy1.setHeightForWidth(self.btn_get_srt.sizePolicy().hasHeightForWidth())
        self.btn_get_srt.setSizePolicy(sizePolicy1)
        self.btn_get_srt.setMinimumSize(QSize(300, 150))

        self.verticalLayout_5.addWidget(self.btn_get_srt)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.formLayout_6 = QFormLayout()
        self.formLayout_6.setObjectName(u"formLayout_6")
        self.formLayout_6.setFormAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_5 = QLabel(self.layoutWidget1)
        self.label_5.setObjectName(u"label_5")
        sizePolicy2.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy2)
        self.label_5.setMinimumSize(QSize(0, 35))

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.label_5)

        self.source_language_srt = QComboBox(self.layoutWidget1)
        self.source_language_srt.setObjectName(u"source_language_srt")
        sizePolicy1.setHeightForWidth(self.source_language_srt.sizePolicy().hasHeightForWidth())
        self.source_language_srt.setSizePolicy(sizePolicy1)
        self.source_language_srt.setMinimumSize(QSize(0, 35))

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.source_language_srt)

        self.horizontalLayout_2.addLayout(self.formLayout_6)

        self.formLayout_7 = QFormLayout()
        self.formLayout_7.setObjectName(u"formLayout_7")
        self.formLayout_7.setFormAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_6 = QLabel(self.layoutWidget1)
        self.label_6.setObjectName(u"label_6")
        sizePolicy2.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy2)
        self.label_6.setMinimumSize(QSize(0, 35))

        self.formLayout_7.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.source_model_srt = QComboBox(self.layoutWidget1)
        self.source_model_srt.setObjectName(u"source_model_srt")
        sizePolicy3.setHeightForWidth(self.source_model_srt.sizePolicy().hasHeightForWidth())
        self.source_model_srt.setSizePolicy(sizePolicy3)
        self.source_model_srt.setMinimumSize(QSize(0, 35))

        self.formLayout_7.setWidget(0, QFormLayout.FieldRole, self.source_model_srt)

        self.horizontalLayout_2.addLayout(self.formLayout_7)

        self.formLayout_8 = QFormLayout()
        self.formLayout_8.setObjectName(u"formLayout_8")
        self.formLayout_8.setFormAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_9 = QLabel(self.layoutWidget1)
        self.label_9.setObjectName(u"label_9")
        sizePolicy2.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy2)
        self.label_9.setMinimumSize(QSize(0, 35))

        self.formLayout_8.setWidget(0, QFormLayout.LabelRole, self.label_9)

        self.translate_type_srt = QComboBox(self.layoutWidget1)
        self.translate_type_srt.setObjectName(u"translate_type_srt")
        sizePolicy3.setHeightForWidth(self.translate_type_srt.sizePolicy().hasHeightForWidth())
        self.translate_type_srt.setSizePolicy(sizePolicy3)
        self.translate_type_srt.setMinimumSize(QSize(0, 35))

        self.formLayout_8.setWidget(0, QFormLayout.FieldRole, self.translate_type_srt)

        self.horizontalLayout_2.addLayout(self.formLayout_8)

        self.formLayout_9 = QFormLayout()
        self.formLayout_9.setObjectName(u"formLayout_9")
        self.formLayout_9.setFormAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_7 = QLabel(self.layoutWidget1)
        self.label_7.setObjectName(u"label_7")
        sizePolicy2.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy2)
        self.label_7.setMinimumSize(QSize(0, 35))

        self.formLayout_9.setWidget(0, QFormLayout.LabelRole, self.label_7)

        self.translate_language_srt = QComboBox(self.layoutWidget1)
        self.translate_language_srt.setObjectName(u"translate_language_srt")
        sizePolicy3.setHeightForWidth(self.translate_language_srt.sizePolicy().hasHeightForWidth())
        self.translate_language_srt.setSizePolicy(sizePolicy3)
        self.translate_language_srt.setMinimumSize(QSize(0, 0))

        self.formLayout_9.setWidget(0, QFormLayout.FieldRole, self.translate_language_srt)

        self.horizontalLayout_2.addLayout(self.formLayout_9)

        self.verticalLayout_5.addLayout(self.horizontalLayout_2)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(80, -1, 80, -1)
        self.srt_table = QTableWidget(self.layoutWidget1)
        if (self.srt_table.columnCount() < 4):
            self.srt_table.setColumnCount(4)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.srt_table.setHorizontalHeaderItem(0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.srt_table.setHorizontalHeaderItem(1, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.srt_table.setHorizontalHeaderItem(2, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.srt_table.setHorizontalHeaderItem(3, __qtablewidgetitem7)
        self.srt_table.setObjectName(u"srt_table")
        sizePolicy4.setHeightForWidth(self.srt_table.sizePolicy().hasHeightForWidth())
        self.srt_table.setSizePolicy(sizePolicy4)
        self.srt_table.setMinimumSize(QSize(0, 300))

        self.verticalLayout_2.addWidget(self.srt_table)

        self.verticalLayout_5.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.startbtn_srt = QPushButton(self.layoutWidget1)
        self.startbtn_srt.setObjectName(u"startbtn_srt")
        sizePolicy5.setHeightForWidth(self.startbtn_srt.sizePolicy().hasHeightForWidth())
        self.startbtn_srt.setSizePolicy(sizePolicy5)
        self.startbtn_srt.setMinimumSize(QSize(200, 50))

        self.verticalLayout_3.addWidget(self.startbtn_srt, 0, Qt.AlignmentFlag.AlignHCenter)

        self.verticalLayout_5.addLayout(self.verticalLayout_3)

        self.stackedWidget.addWidget(self.page_2)
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.video_wiget = QOpenGLWidget(self.page_3)
        self.video_wiget.setObjectName(u"video_wiget")
        self.video_wiget.setGeometry(QRect(40, 30, 300, 200))
        self.eduit_zimu = QTableWidget(self.page_3)
        if (self.eduit_zimu.columnCount() < 6):
            self.eduit_zimu.setColumnCount(6)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.eduit_zimu.setHorizontalHeaderItem(0, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.eduit_zimu.setHorizontalHeaderItem(1, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.eduit_zimu.setHorizontalHeaderItem(2, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.eduit_zimu.setHorizontalHeaderItem(3, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.eduit_zimu.setHorizontalHeaderItem(4, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.eduit_zimu.setHorizontalHeaderItem(5, __qtablewidgetitem13)
        self.eduit_zimu.setObjectName(u"eduit_zimu")
        self.eduit_zimu.setGeometry(QRect(350, 20, 661, 351))
        self.stackedWidget.addWidget(self.page_3)
        self.page_4 = QWidget()
        self.page_4.setObjectName(u"page_4")
        self.label = QLabel(self.page_4)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(440, 300, 201, 81))
        self.stackedWidget.addWidget(self.page_4)
        self.page_5 = QWidget()
        self.page_5.setObjectName(u"page_5")
        self.stackedWidget_2 = QStackedWidget(self.page_5)
        self.stackedWidget_2.setObjectName(u"stackedWidget_2")
        self.stackedWidget_2.setGeometry(QRect(90, 0, 621, 361))
        self.page_10 = QWidget()
        self.page_10.setObjectName(u"page_10")
        self.label_16 = QLabel(self.page_10)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setGeometry(QRect(20, 70, 121, 16))
        self.label_17 = QLabel(self.page_10)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setGeometry(QRect(9, 184, 90, 20))
        self.layoutWidget_4 = QWidget(self.page_10)
        self.layoutWidget_4.setObjectName(u"layoutWidget_4")
        self.layoutWidget_4.setGeometry(QRect(9, 9, 271, 51))
        self.model_type = QHBoxLayout(self.layoutWidget_4)
        self.model_type.setObjectName(u"model_type")
        self.model_type.setContentsMargins(0, 0, 0, 0)
        self.mac_fast = QPushButton(self.layoutWidget_4)
        self.mac_fast.setObjectName(u"mac_fast")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.mac_fast.sizePolicy().hasHeightForWidth())
        self.mac_fast.setSizePolicy(sizePolicy6)

        self.model_type.addWidget(self.mac_fast)

        self.cuda_fust = QPushButton(self.layoutWidget_4)
        self.cuda_fust.setObjectName(u"cuda_fust")
        sizePolicy6.setHeightForWidth(self.cuda_fust.sizePolicy().hasHeightForWidth())
        self.cuda_fust.setSizePolicy(sizePolicy6)

        self.model_type.addWidget(self.cuda_fust)

        self.layoutWidget_5 = QWidget(self.page_10)
        self.layoutWidget_5.setObjectName(u"layoutWidget_5")
        self.layoutWidget_5.setGeometry(QRect(10, 220, 301, 33))
        self.horizontalLayout_12 = QHBoxLayout(self.layoutWidget_5)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.model_save_path = QLineEdit(self.layoutWidget_5)
        self.model_save_path.setObjectName(u"model_save_path")

        self.horizontalLayout_12.addWidget(self.model_save_path)

        self.setting_model_change_dir = QPushButton(self.layoutWidget_5)
        self.setting_model_change_dir.setObjectName(u"setting_model_change_dir")

        self.horizontalLayout_12.addWidget(self.setting_model_change_dir)

        self.stackedWidget_2.addWidget(self.page_10)
        self.page_11 = QWidget()
        self.page_11.setObjectName(u"page_11")
        self.layoutWidget_6 = QWidget(self.page_11)
        self.layoutWidget_6.setObjectName(u"layoutWidget_6")
        self.layoutWidget_6.setGeometry(QRect(20, 20, 319, 88))
        self.verticalLayout_6 = QVBoxLayout(self.layoutWidget_6)
        self.verticalLayout_6.setSpacing(20)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_18 = QLabel(self.layoutWidget_6)
        self.label_18.setObjectName(u"label_18")

        self.horizontalLayout_13.addWidget(self.label_18)

        self.save_dir_openai = QLineEdit(self.layoutWidget_6)
        self.save_dir_openai.setObjectName(u"save_dir_openai")

        self.horizontalLayout_13.addWidget(self.save_dir_openai)

        self.change_dir_9 = QPushButton(self.layoutWidget_6)
        self.change_dir_9.setObjectName(u"change_dir_9")

        self.horizontalLayout_13.addWidget(self.change_dir_9)

        self.verticalLayout_6.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.label_19 = QLabel(self.layoutWidget_6)
        self.label_19.setObjectName(u"label_19")

        self.horizontalLayout_14.addWidget(self.label_19)

        self.save_dir_zhipuai = QLineEdit(self.layoutWidget_6)
        self.save_dir_zhipuai.setObjectName(u"save_dir_zhipuai")

        self.horizontalLayout_14.addWidget(self.save_dir_zhipuai)

        self.change_dir_10 = QPushButton(self.layoutWidget_6)
        self.change_dir_10.setObjectName(u"change_dir_10")

        self.horizontalLayout_14.addWidget(self.change_dir_10)

        self.verticalLayout_6.addLayout(self.horizontalLayout_14)

        self.stackedWidget_2.addWidget(self.page_11)
        self.page_12 = QWidget()
        self.page_12.setObjectName(u"page_12")
        self.layoutWidget_7 = QWidget(self.page_12)
        self.layoutWidget_7.setObjectName(u"layoutWidget_7")
        self.layoutWidget_7.setGeometry(QRect(20, 20, 341, 141))
        self.verticalLayout_7 = QVBoxLayout(self.layoutWidget_7)
        self.verticalLayout_7.setSpacing(20)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.label_20 = QLabel(self.layoutWidget_7)
        self.label_20.setObjectName(u"label_20")

        self.horizontalLayout_15.addWidget(self.label_20)

        self.save_dir_baidu = QLineEdit(self.layoutWidget_7)
        self.save_dir_baidu.setObjectName(u"save_dir_baidu")

        self.horizontalLayout_15.addWidget(self.save_dir_baidu)

        self.change_dir_11 = QPushButton(self.layoutWidget_7)
        self.change_dir_11.setObjectName(u"change_dir_11")

        self.horizontalLayout_15.addWidget(self.change_dir_11)

        self.verticalLayout_7.addLayout(self.horizontalLayout_15)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.label_21 = QLabel(self.layoutWidget_7)
        self.label_21.setObjectName(u"label_21")

        self.horizontalLayout_16.addWidget(self.label_21)

        self.save_dir_tengxun = QLineEdit(self.layoutWidget_7)
        self.save_dir_tengxun.setObjectName(u"save_dir_tengxun")

        self.horizontalLayout_16.addWidget(self.save_dir_tengxun)

        self.change_dir_12 = QPushButton(self.layoutWidget_7)
        self.change_dir_12.setObjectName(u"change_dir_12")

        self.horizontalLayout_16.addWidget(self.change_dir_12)

        self.verticalLayout_7.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.label_22 = QLabel(self.layoutWidget_7)
        self.label_22.setObjectName(u"label_22")

        self.horizontalLayout_17.addWidget(self.label_22)

        self.save_dir_deel = QLineEdit(self.layoutWidget_7)
        self.save_dir_deel.setObjectName(u"save_dir_deel")

        self.horizontalLayout_17.addWidget(self.save_dir_deel)

        self.change_dir_13 = QPushButton(self.layoutWidget_7)
        self.change_dir_13.setObjectName(u"change_dir_13")

        self.horizontalLayout_17.addWidget(self.change_dir_13)

        self.verticalLayout_7.addLayout(self.horizontalLayout_17)

        self.stackedWidget_2.addWidget(self.page_12)
        self.page_13 = QWidget()
        self.page_13.setObjectName(u"page_13")
        self.layoutWidget_8 = QWidget(self.page_13)
        self.layoutWidget_8.setObjectName(u"layoutWidget_8")
        self.layoutWidget_8.setGeometry(QRect(20, 20, 301, 135))
        self.verticalLayout_8 = QVBoxLayout(self.layoutWidget_8)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_23 = QLabel(self.layoutWidget_8)
        self.label_23.setObjectName(u"label_23")

        self.verticalLayout_8.addWidget(self.label_23)

        self.proxy_no = QCheckBox(self.layoutWidget_8)
        self.proxy_no.setObjectName(u"proxy_no")
        sizePolicy3.setHeightForWidth(self.proxy_no.sizePolicy().hasHeightForWidth())
        self.proxy_no.setSizePolicy(sizePolicy3)
        self.proxy_no.setMinimumSize(QSize(0, 35))

        self.verticalLayout_8.addWidget(self.proxy_no)

        self.proxy_use = QCheckBox(self.layoutWidget_8)
        self.proxy_use.setObjectName(u"proxy_use")
        sizePolicy3.setHeightForWidth(self.proxy_use.sizePolicy().hasHeightForWidth())
        self.proxy_use.setSizePolicy(sizePolicy3)
        self.proxy_use.setMinimumSize(QSize(0, 35))

        self.verticalLayout_8.addWidget(self.proxy_use)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalLayout_18.setContentsMargins(15, -1, -1, -1)
        self.proxy = QLineEdit(self.layoutWidget_8)
        self.proxy.setObjectName(u"proxy")

        self.horizontalLayout_18.addWidget(self.proxy)

        self.change_dir_14 = QPushButton(self.layoutWidget_8)
        self.change_dir_14.setObjectName(u"change_dir_14")

        self.horizontalLayout_18.addWidget(self.change_dir_14)

        self.verticalLayout_8.addLayout(self.horizontalLayout_18)

        self.stackedWidget_2.addWidget(self.page_13)
        self.memu_settling = QListWidget(self.page_5)
        QListWidgetItem(self.memu_settling)
        QListWidgetItem(self.memu_settling)
        QListWidgetItem(self.memu_settling)
        QListWidgetItem(self.memu_settling)
        self.memu_settling.setObjectName(u"memu_settling")
        self.memu_settling.setGeometry(QRect(0, 0, 90, 369))
        sizePolicy.setHeightForWidth(self.memu_settling.sizePolicy().hasHeightForWidth())
        self.memu_settling.setSizePolicy(sizePolicy)
        self.memu_settling.setMaximumSize(QSize(90, 16777215))
        self.stackedWidget.addWidget(self.page_5)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 930, 24))
        self.menu_2 = QMenu(self.menubar)
        self.menu_2.setObjectName(u"menu_2")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menu_2.menuAction())
        self.menu_2.addAction(self.action)
        self.menu_2.addAction(self.action_2)

        self.retranslateUi(MainWindow)
        self.listWidget.currentRowChanged.connect(self.stackedWidget.setCurrentIndex)
        self.memu_settling.currentRowChanged.connect(self.stackedWidget_2.setCurrentIndex)

        self.stackedWidget.setCurrentIndex(0)
        self.stackedWidget_2.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.action.setText(QCoreApplication.translate("MainWindow", u"充值算力", None))
        self.action_2.setText(QCoreApplication.translate("MainWindow", u"兑换码", None))

        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        ___qlistwidgetitem = self.listWidget.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("MainWindow", u"音视频转字幕", None));
        ___qlistwidgetitem1 = self.listWidget.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("MainWindow", u"字幕翻译", None));
        ___qlistwidgetitem2 = self.listWidget.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("MainWindow", u"编辑字幕", None));
        ___qlistwidgetitem3 = self.listWidget.item(3)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("MainWindow", u"我的创作", None));
        ___qlistwidgetitem4 = self.listWidget.item(4)
        ___qlistwidgetitem4.setText(QCoreApplication.translate("MainWindow", u"我的设置", None));
        self.listWidget.setSortingEnabled(__sortingEnabled)

        self.btn_get_video.setText(QCoreApplication.translate("MainWindow", u"导入音视频文件", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u" 原始语种", None))
        #if QT_CONFIG(tooltip)
        self.source_language.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        #endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"识别引擎", None))
        #if QT_CONFIG(tooltip)
        self.source_model.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        #endif // QT_CONFIG(tooltip)
        #if QT_CONFIG(tooltip)
        self.check_fanyi.setToolTip(
            QCoreApplication.translate("MainWindow", u"必须确定有NVIDIA显卡且正确配置了CUDA环境，否则勿选", None))
        #endif // QT_CONFIG(tooltip)
        self.check_fanyi.setText(QCoreApplication.translate("MainWindow", u"字幕翻译", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"翻译引擎", None))
        #if QT_CONFIG(tooltip)
        self.translate_type.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        #endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"翻译语种", None))
        #if QT_CONFIG(tooltip)
        self.translate_language.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        #endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem = self.media_table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"文件名", None));
        ___qtablewidgetitem1 = self.media_table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"时长", None));
        ___qtablewidgetitem2 = self.media_table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"算力消耗", None));
        ___qtablewidgetitem3 = self.media_table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"操作", None));
        self.startbtn_1.setText(QCoreApplication.translate("MainWindow", u"开始111", None))

        self.btn_get_srt.setText(QCoreApplication.translate("MainWindow", u"导入字幕文件", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u" 原始语种", None))
        #if QT_CONFIG(tooltip)
        self.source_language_srt.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        #endif // QT_CONFIG(tooltip)
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"识别引擎", None))
        #if QT_CONFIG(tooltip)
        self.source_model_srt.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        #endif // QT_CONFIG(tooltip)
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"翻译引擎", None))
        #if QT_CONFIG(tooltip)
        self.translate_type_srt.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        #endif // QT_CONFIG(tooltip)
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"翻译语种", None))
        #if QT_CONFIG(tooltip)
        self.translate_language_srt.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        #endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem4 = self.srt_table.horizontalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"文件名", None));
        ___qtablewidgetitem5 = self.srt_table.horizontalHeaderItem(1)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"时长", None));
        ___qtablewidgetitem6 = self.srt_table.horizontalHeaderItem(2)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MainWindow", u"算力消耗", None));
        ___qtablewidgetitem7 = self.srt_table.horizontalHeaderItem(3)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("MainWindow", u"操作", None));
        self.startbtn_srt.setText(QCoreApplication.translate("MainWindow", u"开始", None))
        ___qtablewidgetitem8 = self.eduit_zimu.horizontalHeaderItem(0)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("MainWindow", u"操作", None));
        ___qtablewidgetitem9 = self.eduit_zimu.horizontalHeaderItem(1)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("MainWindow", u"新建列", None));
        ___qtablewidgetitem10 = self.eduit_zimu.horizontalHeaderItem(2)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("MainWindow", u"时长", None));
        ___qtablewidgetitem11 = self.eduit_zimu.horizontalHeaderItem(3)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("MainWindow", u"新建列", None));
        ___qtablewidgetitem12 = self.eduit_zimu.horizontalHeaderItem(4)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("MainWindow", u"原文", None));
        ___qtablewidgetitem13 = self.eduit_zimu.horizontalHeaderItem(5)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("MainWindow", u"编辑", None));
        self.label.setText(QCoreApplication.translate("MainWindow", u"我的创作页", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"使用本地模型", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow",
                                                         u"<html><head/><body><p><span style=\" font-size:11pt; font-weight:700;\">模型存放路径</span></p></body></html>",
                                                         None))
        self.mac_fast.setText(QCoreApplication.translate("MainWindow", u"mac加速", None))
        self.cuda_fust.setText(QCoreApplication.translate("MainWindow", u"cuda加速", None))
        self.setting_model_change_dir.setText(QCoreApplication.translate("MainWindow", u"更换路径", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow",
                                                         u"<html><head/><body><p><span style=\" font-weight:700;\">OpenAI APi Key</span></p></body></html>",
                                                         None))
        self.change_dir_9.setText(QCoreApplication.translate("MainWindow", u"保存", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow",
                                                         u"<html><head/><body><p><span style=\" font-weight:700;\">智谱AI APi Key</span></p></body></html>",
                                                         None))
        self.change_dir_10.setText(QCoreApplication.translate("MainWindow", u"保存", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow",
                                                         u"<html><head/><body><p><span style=\" font-weight:700;\">百度翻译</span></p></body></html>",
                                                         None))
        self.change_dir_11.setText(QCoreApplication.translate("MainWindow", u"保存", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow",
                                                         u"<html><head/><body><p><span style=\" font-weight:700;\">腾讯翻译</span></p></body></html>",
                                                         None))
        self.change_dir_12.setText(QCoreApplication.translate("MainWindow", u"保存", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow",
                                                         u"<html><head/><body><p><span style=\" font-weight:700;\">Deepl翻译</span></p></body></html>",
                                                         None))
        self.change_dir_13.setText(QCoreApplication.translate("MainWindow", u"保存", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow",
                                                         u"<html><head/><body><p><span style=\" font-weight:700;\">代理设置</span></p></body></html>",
                                                         None))
        #if QT_CONFIG(tooltip)
        self.proxy_no.setToolTip(
            QCoreApplication.translate("MainWindow", u"必须确定有NVIDIA显卡且正确配置了CUDA环境，否则勿选", None))
        #endif // QT_CONFIG(tooltip)
        self.proxy_no.setText(QCoreApplication.translate("MainWindow", u"无代理", None))
        #if QT_CONFIG(tooltip)
        self.proxy_use.setToolTip(
            QCoreApplication.translate("MainWindow", u"必须确定有NVIDIA显卡且正确配置了CUDA环境，否则勿选", None))
        #endif // QT_CONFIG(tooltip)
        self.proxy_use.setText(QCoreApplication.translate("MainWindow", u"使用代理", None))
        self.change_dir_14.setText(QCoreApplication.translate("MainWindow", u"保存", None))

        __sortingEnabled1 = self.memu_settling.isSortingEnabled()
        self.memu_settling.setSortingEnabled(False)
        ___qlistwidgetitem5 = self.memu_settling.item(0)
        ___qlistwidgetitem5.setText(QCoreApplication.translate("MainWindow", u"本地模型", None));
        ___qlistwidgetitem6 = self.memu_settling.item(1)
        ___qlistwidgetitem6.setText(QCoreApplication.translate("MainWindow", u"LLM配置", None));
        ___qlistwidgetitem7 = self.memu_settling.item(2)
        ___qlistwidgetitem7.setText(QCoreApplication.translate("MainWindow", u"翻译设置", None));
        ___qlistwidgetitem8 = self.memu_settling.item(3)
        ___qlistwidgetitem8.setText(QCoreApplication.translate("MainWindow", u"代理设置", None));
        self.memu_settling.setSortingEnabled(__sortingEnabled1)

        self.menu_2.setTitle(QCoreApplication.translate("MainWindow", u"登陆", None))  # retranslateUi
