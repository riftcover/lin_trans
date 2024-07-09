from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect)

from PySide6.QtWidgets import (QLabel, QMenuBar, QStackedWidget,
                               QStatusBar, QVBoxLayout,
                               QWidget)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(930, 674)

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)

        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setGeometry(QRect(10, 10, 910, 620))

        # Page 1
        self.page1 = QWidget()
        self.page1.setObjectName(u"page1")
        self.stackedWidget.addWidget(self.page1)

        # Page 2
        self.page2 = QWidget()
        self.page2.setObjectName(u"page2")
        self.stackedWidget.addWidget(self.page2)

        # Example layout for Page 1
        self.layout1 = QVBoxLayout(self.page1)
        self.label1 = QLabel("Page 1", self.page1)
        self.layout1.addWidget(self.label1)

        # Example layout for Page 2
        self.layout2 = QVBoxLayout(self.page2)
        self.label2 = QLabel("Page 2", self.page2)
        self.layout2.addWidget(self.label2)

        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 930, 22))
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.stackedWidget.setCurrentIndex(0)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label1.setText(QCoreApplication.translate("MainWindow", u"Page 1", None))
        self.label2.setText(QCoreApplication.translate("MainWindow", u"Page 2", None))
