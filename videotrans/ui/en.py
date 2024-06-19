# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'linlin.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QStackedWidget, QStatusBar,
    QTableWidget, QTableWidgetItem, QToolBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1626, 1034)
        self.action_tiquzimu_no = QAction(MainWindow)
        self.action_tiquzimu_no.setObjectName(u"action_tiquzimu_no")
        icon = QIcon(QIcon.fromTheme(u"从本地视频中提取出原始语言的srt字幕"))
        self.action_tiquzimu_no.setIcon(icon)
        self.action_tiquzimu_no.setMenuRole(QAction.MenuRole.TextHeuristicRole)
        self.action_fanyi = QAction(MainWindow)
        self.action_fanyi.setObjectName(u"action_fanyi")
        self.action_fanyi.setMenuRole(QAction.MenuRole.TextHeuristicRole)
        self.action_eduit = QAction(MainWindow)
        self.action_eduit.setObjectName(u"action_eduit")
        self.action_eduit.setMenuRole(QAction.MenuRole.TextHeuristicRole)
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
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setGeometry(QRect(0, 0, 101, 801))
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setGeometry(QRect(100, 0, 1241, 801))
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.widget = QWidget(self.page)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(10, 10, 1221, 781))
        self.verticalLayout_1 = QVBoxLayout(self.widget)
        self.verticalLayout_1.setSpacing(30)
        self.verticalLayout_1.setObjectName(u"verticalLayout_1")
        self.verticalLayout_1.setContentsMargins(0, 10, 0, 0)
        self.pushButton = QPushButton(self.widget)
        self.pushButton.setObjectName(u"pushButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setMinimumSize(QSize(300, 150))

        self.verticalLayout_1.addWidget(self.pushButton)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy1)
        self.label_2.setMinimumSize(QSize(0, 35))

        self.horizontalLayout.addWidget(self.label_2)

        self.source_language = QComboBox(self.widget)
        self.source_language.setObjectName(u"source_language")
        sizePolicy.setHeightForWidth(self.source_language.sizePolicy().hasHeightForWidth())
        self.source_language.setSizePolicy(sizePolicy)
        self.source_language.setMinimumSize(QSize(0, 35))

        self.horizontalLayout.addWidget(self.source_language)


        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")
        sizePolicy1.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy1)
        self.label_3.setMinimumSize(QSize(0, 35))

        self.horizontalLayout_3.addWidget(self.label_3)

        self.source_language_2 = QComboBox(self.widget)
        self.source_language_2.setObjectName(u"source_language_2")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.source_language_2.sizePolicy().hasHeightForWidth())
        self.source_language_2.setSizePolicy(sizePolicy2)
        self.source_language_2.setMinimumSize(QSize(0, 35))

        self.horizontalLayout_3.addWidget(self.source_language_2)

        self.enable_cuda = QCheckBox(self.widget)
        self.enable_cuda.setObjectName(u"enable_cuda")
        sizePolicy2.setHeightForWidth(self.enable_cuda.sizePolicy().hasHeightForWidth())
        self.enable_cuda.setSizePolicy(sizePolicy2)
        self.enable_cuda.setMinimumSize(QSize(0, 35))

        self.horizontalLayout_3.addWidget(self.enable_cuda)


        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 1, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_4 = QLabel(self.widget)
        self.label_4.setObjectName(u"label_4")
        sizePolicy1.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy1)
        self.label_4.setMinimumSize(QSize(0, 35))

        self.horizontalLayout_2.addWidget(self.label_4)

        self.source_language_3 = QComboBox(self.widget)
        self.source_language_3.setObjectName(u"source_language_3")
        sizePolicy2.setHeightForWidth(self.source_language_3.sizePolicy().hasHeightForWidth())
        self.source_language_3.setSizePolicy(sizePolicy2)
        self.source_language_3.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_2.addWidget(self.source_language_3)


        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 2, 1, 1)


        self.verticalLayout_1.addLayout(self.gridLayout)

        self.tableWidget = QTableWidget(self.widget)
        if (self.tableWidget.columnCount() < 4):
            self.tableWidget.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.tableWidget.setObjectName(u"tableWidget")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy3)
        self.tableWidget.setMinimumSize(QSize(0, 300))

        self.verticalLayout_1.addWidget(self.tableWidget)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.startbtn_2 = QPushButton(self.widget)
        self.startbtn_2.setObjectName(u"startbtn_2")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.startbtn_2.sizePolicy().hasHeightForWidth())
        self.startbtn_2.setSizePolicy(sizePolicy4)
        self.startbtn_2.setMinimumSize(QSize(200, 50))

        self.verticalLayout.addWidget(self.startbtn_2, 0, Qt.AlignmentFlag.AlignHCenter)


        self.verticalLayout_1.addLayout(self.verticalLayout)

        self.stackedWidget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.layoutWidget = QWidget(self.page_2)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(10, 10, 1221, 781))
        self.verticalLayout_2 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_2.setSpacing(30)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 10, 0, 0)
        self.pushButton_2 = QPushButton(self.layoutWidget)
        self.pushButton_2.setObjectName(u"pushButton_2")
        sizePolicy.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy)
        self.pushButton_2.setMinimumSize(QSize(300, 150))

        self.verticalLayout_2.addWidget(self.pushButton_2)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_5 = QLabel(self.layoutWidget)
        self.label_5.setObjectName(u"label_5")
        sizePolicy1.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy1)
        self.label_5.setMinimumSize(QSize(0, 35))

        self.horizontalLayout_5.addWidget(self.label_5)

        self.source_language_4 = QComboBox(self.layoutWidget)
        self.source_language_4.setObjectName(u"source_language_4")
        sizePolicy.setHeightForWidth(self.source_language_4.sizePolicy().hasHeightForWidth())
        self.source_language_4.setSizePolicy(sizePolicy)
        self.source_language_4.setMinimumSize(QSize(0, 35))

        self.horizontalLayout_5.addWidget(self.source_language_4)


        self.gridLayout_2.addLayout(self.horizontalLayout_5, 0, 0, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_6 = QLabel(self.layoutWidget)
        self.label_6.setObjectName(u"label_6")
        sizePolicy1.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy1)
        self.label_6.setMinimumSize(QSize(0, 35))

        self.horizontalLayout_6.addWidget(self.label_6)

        self.source_language_5 = QComboBox(self.layoutWidget)
        self.source_language_5.setObjectName(u"source_language_5")
        sizePolicy2.setHeightForWidth(self.source_language_5.sizePolicy().hasHeightForWidth())
        self.source_language_5.setSizePolicy(sizePolicy2)
        self.source_language_5.setMinimumSize(QSize(0, 35))

        self.horizontalLayout_6.addWidget(self.source_language_5)

        self.enable_cuda_2 = QCheckBox(self.layoutWidget)
        self.enable_cuda_2.setObjectName(u"enable_cuda_2")
        sizePolicy2.setHeightForWidth(self.enable_cuda_2.sizePolicy().hasHeightForWidth())
        self.enable_cuda_2.setSizePolicy(sizePolicy2)
        self.enable_cuda_2.setMinimumSize(QSize(0, 35))

        self.horizontalLayout_6.addWidget(self.enable_cuda_2)


        self.gridLayout_2.addLayout(self.horizontalLayout_6, 0, 1, 1, 1)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_7 = QLabel(self.layoutWidget)
        self.label_7.setObjectName(u"label_7")
        sizePolicy1.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy1)
        self.label_7.setMinimumSize(QSize(0, 35))

        self.horizontalLayout_7.addWidget(self.label_7)

        self.source_language_6 = QComboBox(self.layoutWidget)
        self.source_language_6.setObjectName(u"source_language_6")
        sizePolicy2.setHeightForWidth(self.source_language_6.sizePolicy().hasHeightForWidth())
        self.source_language_6.setSizePolicy(sizePolicy2)
        self.source_language_6.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_7.addWidget(self.source_language_6)


        self.gridLayout_2.addLayout(self.horizontalLayout_7, 0, 2, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_2)

        self.tableWidget_2 = QTableWidget(self.layoutWidget)
        if (self.tableWidget_2.columnCount() < 4):
            self.tableWidget_2.setColumnCount(4)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(1, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(2, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(3, __qtablewidgetitem7)
        self.tableWidget_2.setObjectName(u"tableWidget_2")
        sizePolicy3.setHeightForWidth(self.tableWidget_2.sizePolicy().hasHeightForWidth())
        self.tableWidget_2.setSizePolicy(sizePolicy3)
        self.tableWidget_2.setMinimumSize(QSize(0, 300))

        self.verticalLayout_2.addWidget(self.tableWidget_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.startbtn_3 = QPushButton(self.layoutWidget)
        self.startbtn_3.setObjectName(u"startbtn_3")
        sizePolicy4.setHeightForWidth(self.startbtn_3.sizePolicy().hasHeightForWidth())
        self.startbtn_3.setSizePolicy(sizePolicy4)
        self.startbtn_3.setMinimumSize(QSize(200, 50))

        self.verticalLayout_3.addWidget(self.startbtn_3, 0, Qt.AlignmentFlag.AlignHCenter)


        self.verticalLayout_2.addLayout(self.verticalLayout_3)

        self.stackedWidget.addWidget(self.page_2)
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.openGLWidget = QOpenGLWidget(self.page_3)
        self.openGLWidget.setObjectName(u"openGLWidget")
        self.openGLWidget.setGeometry(QRect(40, 30, 300, 200))
        self.tableWidget_3 = QTableWidget(self.page_3)
        if (self.tableWidget_3.columnCount() < 6):
            self.tableWidget_3.setColumnCount(6)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableWidget_3.setHorizontalHeaderItem(0, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tableWidget_3.setHorizontalHeaderItem(1, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tableWidget_3.setHorizontalHeaderItem(2, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tableWidget_3.setHorizontalHeaderItem(3, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.tableWidget_3.setHorizontalHeaderItem(4, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.tableWidget_3.setHorizontalHeaderItem(5, __qtablewidgetitem13)
        self.tableWidget_3.setObjectName(u"tableWidget_3")
        self.tableWidget_3.setGeometry(QRect(350, 20, 781, 371))
        self.stackedWidget.addWidget(self.page_3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1626, 33))
        self.menu = QMenu(self.menubar)
        self.menu.setObjectName(u"menu")
        self.menu_2 = QMenu(self.menubar)
        self.menu_2.setObjectName(u"menu_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        MainWindow.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.toolBar)

        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())
        self.menu_2.addAction(self.action)
        self.menu_2.addAction(self.action_2)

        self.retranslateUi(MainWindow)
        self.listWidget.currentRowChanged.connect(self.stackedWidget.setCurrentIndex)

        self.stackedWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.action_tiquzimu_no.setText(QCoreApplication.translate("MainWindow", u"音视频转字幕", None))
#if QT_CONFIG(tooltip)
        self.action_tiquzimu_no.setToolTip(QCoreApplication.translate("MainWindow", u"音视频转字幕", None))
#endif // QT_CONFIG(tooltip)
        self.action_fanyi.setText(QCoreApplication.translate("MainWindow", u"文本字幕翻译", None))
#if QT_CONFIG(tooltip)
        self.action_fanyi.setToolTip(QCoreApplication.translate("MainWindow", u"字幕翻译", None))
#endif // QT_CONFIG(tooltip)
        self.action_eduit.setText(QCoreApplication.translate("MainWindow", u"编辑字幕", None))
#if QT_CONFIG(tooltip)
        self.action_eduit.setToolTip(QCoreApplication.translate("MainWindow", u"编辑srt字幕文件", None))
#endif // QT_CONFIG(tooltip)
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
        self.listWidget.setSortingEnabled(__sortingEnabled)

        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"导入音视频文件", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u" 原始语种", None))
#if QT_CONFIG(tooltip)
        self.source_language.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
#endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"识别引擎", None))
#if QT_CONFIG(tooltip)
        self.source_language_2.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.enable_cuda.setToolTip(QCoreApplication.translate("MainWindow", u"必须确定有NVIDIA显卡且正确配置了CUDA环境，否则勿选", None))
#endif // QT_CONFIG(tooltip)
        self.enable_cuda.setText(QCoreApplication.translate("MainWindow", u"字幕翻译", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"翻译语种", None))
#if QT_CONFIG(tooltip)
        self.source_language_3.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
#endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"新建列", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"文件名", None));
        ___qtablewidgetitem2 = self.tableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"时长", None));
        ___qtablewidgetitem3 = self.tableWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"操作", None));
        self.startbtn_2.setText(QCoreApplication.translate("MainWindow", u"开始", None))
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"导入字幕文件", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u" 原始语种", None))
#if QT_CONFIG(tooltip)
        self.source_language_4.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
#endif // QT_CONFIG(tooltip)
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"识别引擎", None))
#if QT_CONFIG(tooltip)
        self.source_language_5.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.enable_cuda_2.setToolTip(QCoreApplication.translate("MainWindow", u"必须确定有NVIDIA显卡且正确配置了CUDA环境，否则勿选", None))
#endif // QT_CONFIG(tooltip)
        self.enable_cuda_2.setText(QCoreApplication.translate("MainWindow", u"字幕翻译", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"翻译语种", None))
#if QT_CONFIG(tooltip)
        self.source_language_6.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
#endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem4 = self.tableWidget_2.horizontalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"新建列", None));
        ___qtablewidgetitem5 = self.tableWidget_2.horizontalHeaderItem(1)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"文件名", None));
        ___qtablewidgetitem6 = self.tableWidget_2.horizontalHeaderItem(2)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MainWindow", u"时长", None));
        ___qtablewidgetitem7 = self.tableWidget_2.horizontalHeaderItem(3)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("MainWindow", u"操作", None));
        self.startbtn_3.setText(QCoreApplication.translate("MainWindow", u"开始", None))
        ___qtablewidgetitem8 = self.tableWidget_3.horizontalHeaderItem(0)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("MainWindow", u"操作", None));
        ___qtablewidgetitem9 = self.tableWidget_3.horizontalHeaderItem(1)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("MainWindow", u"新建列", None));
        ___qtablewidgetitem10 = self.tableWidget_3.horizontalHeaderItem(2)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("MainWindow", u"时长", None));
        ___qtablewidgetitem11 = self.tableWidget_3.horizontalHeaderItem(3)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("MainWindow", u"新建列", None));
        ___qtablewidgetitem12 = self.tableWidget_3.horizontalHeaderItem(4)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("MainWindow", u"原文", None));
        ___qtablewidgetitem13 = self.tableWidget_3.horizontalHeaderItem(5)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("MainWindow", u"编辑", None));
        self.menu.setTitle(QCoreApplication.translate("MainWindow", u"设置", None))
        self.menu_2.setTitle(QCoreApplication.translate("MainWindow", u"登陆", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar", None))
    # retranslateUi

