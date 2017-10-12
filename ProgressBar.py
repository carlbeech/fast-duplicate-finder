from PyQt5 import QtCore, QtGui, QtWidgets
import sys

from ProgressDialog import Ui_Dialog



class ProgressDlg(QtWidgets.QDialog, Ui_Dialog):
    CloseClicked = 0

    def __init__(self, ProgressBar_CLOSE, desc = None, parent=None):
        super(ProgressDlg, self).__init__(parent)
        self.setupUi(self)
        self.show()

        print ("Progressbar_CLOSE:"+str(ProgressBar_CLOSE))

        self.CancelButton.clicked.connect(self.pbCloseClicked)

        if desc != None:
            self.setDescription(desc)

    def setValue(self, val): # Sets value
        self.progressBar.setProperty("value", val)

    def setTotalFiles(self, desc):
        self.FileCounter.setText(desc)

    def setProgressText(self, desc):
        self.ProgressText.setText(desc)

    def pbCloseClicked(self):

        print("CloseClicked")

        self.close()

        self.CloseClicked=1

    def GetCloseStatus(self):
        return self.CloseClicked

def main():
    app = QtWidgets.QApplication(sys.argv)      # A new instance of QApplication
    form = ProgressBar('pbar')                        # We set the form to be our MainWindow (design)
    app.exec_()                                 # and execute the app

if __name__ == '__main__':                      # if we're running file directly and not importing it
    main()                                      # run the main function



