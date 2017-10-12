#! /usr/bin/python3
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from fdf_main import Ui_MainWindow


def GetFile(self):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName = QFileDialog.getOpenFileName(self, 'Open file', '.', 'OpenFile(*)')
    if fileName:
        # self.Databasefile.setText(fileName[0])
        return fileName[0]
    else:
        return ""


def GetDir(self):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
    if fileName:
        # self.Databasefile.setText(fileName[0])
        return fileName
    else:
        return ""

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.setupUi(self)

        # Connect "add" button with a custom function (addInputTextToListbox)
        self.Databasefile_Elipsis.clicked.connect(self.DBFileDialog)
        self.Configurationfile_Elipsis.clicked.connect(self.ConfFileDialog)
        self.Outputscript_Elipsis.clicked.connect(self.OutputFileDialog)

        # Connect "add" button with a custom function
        self.SearchDirectory_ADD.clicked.connect(self.AddSearchDirectory)
        self.SearchDirectory_DEL.clicked.connect(self.DelSearchDirectory)
        self.PreserveDirectory_ADD.clicked.connect(self.AddPreserveDirectory)
        self.PreserveDirectory_DEL.clicked.connect(self.DelPreserveDirectory)

    def DBFileDialog(self):

        tfile=""
        tfile=GetFile(self)
        if len(tfile)>0:
            self.Databasefile.setText(tfile)

    def ConfFileDialog(self):

        tfile=""
        tfile=GetFile(self)
        if len(tfile)>0:
            self.Configurationfile.setText(tfile)

    def OutputFileDialog(self):

        tfile=""
        tfile=GetFile(self)
        if len(tfile)>0:
            self.Outputscript.setText(tfile)


    def AddSearchDirectory(self):
        tfile=""
        tfile=GetDir(self)
        if len(tfile)>0:
            self.SearchDirectoryList.addItem(tfile)

    def DelSearchDirectory(self):
        listItems = self.SearchDirectoryList.selectedItems()
        if not listItems: return
        for item in listItems:
            self.SearchDirectoryList.takeItem(self.SearchDirectoryList.row(item))

    def AddPreserveDirectory(self):
        tfile = ""
        tfile = GetDir(self)
        if len(tfile) > 0:
            self.PreserveDirectoryList.addItem(tfile)

    def DelPreserveDirectory(self):
        listItems = self.PreserveDirectoryList.selectedItems()
        if not listItems: return
        for item in listItems:
            self.PreserveDirectoryList.takeItem(self.PreserveDirectoryList.row(item))


import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())