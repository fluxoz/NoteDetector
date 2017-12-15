
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from LiveAudio import AudioStream, Thread
import os

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1072, 600)

        #clickchecker
        self.clicked = False

        #AudioStream/Timer object
        self.plot = Thread()

        #form setup and configuration
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.LiveAudioButton = QtWidgets.QPushButton(self.centralwidget)
        self.LiveAudioButton.setGeometry(QtCore.QRect(50, 90, 99, 27))
        self.LiveAudioButton.setObjectName("LiveAudioButton")
        self.LiveAudioButton.clicked.connect(self.liveaudioclick)

        #self.FileButton = QtWidgets.QPushButton(self.centralwidget)
        #self.FileButton.setGeometry(QtCore.QRect(50, 140, 99, 27))
        #self.FileButton.setObjectName("FileButton")
        #self.FileButton.clicked.connect(self.getfile)

        #create a Frame and insert graphicslayoutwidget
        self.frame = QtGui.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(180, 20, 871, 561))
        self.layout = QtGui.QGridLayout()
        self.frame.setLayout(self.layout)
        self.layout.addWidget(self.plot.stream.win, * (0,1))

        self.NoteOutput = QtGui.QFrame(self.centralwidget)
        self.NoteOutput.setGeometry(QtCore.QRect(40, 320, 120, 80))
        self.layout2 = QtGui.QGridLayout()
        self.NoteOutput.setLayout(self.layout2)
        self.layout2.addWidget(self.plot.stream.notebox, * (0,1))

        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)



    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "NoteDetector"))
        self.LiveAudioButton.setText(_translate("MainWindow", "Live Audio"))
        #self.FileButton.setText(_translate("MainWindow", ".wav File"))

    def liveaudioclick(self):
        if self.clicked == True:
            self.clicked = False
            self.plot.stop()
        else:
            self.clicked = True
            self.plot.run()

    #def getfile(self):
        #filename = QtGui.QFileDialog.getOpenFileName(None, 'Open .wav file', os.getenv('HOME'))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication.instance()
    if app is None:
        app = QtGui.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

