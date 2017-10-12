# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'AboutDialog.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        AboutDialog.setObjectName("AboutDialog")
        AboutDialog.resize(400, 300)
        AboutDialog.setMinimumSize(QtCore.QSize(400, 300))
        AboutDialog.setMaximumSize(QtCore.QSize(400, 300))
        self.OkButton = QtWidgets.QPushButton(AboutDialog)
        self.OkButton.setGeometry(QtCore.QRect(290, 250, 88, 34))
        self.OkButton.setObjectName("OkButton")
        self.ProgramText = QtWidgets.QLabel(AboutDialog)
        self.ProgramText.setGeometry(QtCore.QRect(10, 10, 371, 18))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.ProgramText.setFont(font)
        self.ProgramText.setObjectName("ProgramText")
        self.VersionText = QtWidgets.QLabel(AboutDialog)
        self.VersionText.setGeometry(QtCore.QRect(10, 50, 371, 141))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.VersionText.setFont(font)
        self.VersionText.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.VersionText.setObjectName("VersionText")

        self.retranslateUi(AboutDialog)
        self.OkButton.clicked.connect(AboutDialog.close)
        QtCore.QMetaObject.connectSlotsByName(AboutDialog)

    def retranslateUi(self, AboutDialog):
        _translate = QtCore.QCoreApplication.translate
        AboutDialog.setWindowTitle(_translate("AboutDialog", "Dialog"))
        self.OkButton.setText(_translate("AboutDialog", "OK"))
        self.ProgramText.setText(_translate("AboutDialog", "ProgramText"))
        self.VersionText.setText(_translate("AboutDialog", "VersionText"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    AboutDialog = QtWidgets.QDialog()
    ui = Ui_AboutDialog()
    ui.setupUi(AboutDialog)
    AboutDialog.show()
    sys.exit(app.exec_())

