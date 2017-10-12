import sys
import os
from PyQt4 import QtCore, QtGui, uic
# from PyQt4.QtGui import QStandardItemModel, QStandardItem
from PyQt4.QtGui import QStandardItem, QStandardItemModel

qtCreatorFile = "FDF_Main.ui" # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

#   Create the filelist
FileList=[[]]

class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.StartProcessing.clicked.connect(self.StartButton)

    def StartButton(self):
        self.ResultsList.addItem('Hello')
        FileList[len(FileList)-1].append("one")
        FileList[len(FileList)-1].append("two")
        FileList.append([])
        FileList[len(FileList)-1].append("three")

        for j in range(1):
            for i in range(1):
                self.ResultsList.addItem(FileList[i][j])

        self.RecurseDirectories("/home/carl/Downloads")

    def RecurseDirectories(self,walk_dir):

        # print('walk_dir = ' + walk_dir)

        # If your current working directory may change during script execution, it's recommended to
        # immediately convert program arguments to an absolute path. Then the variable root below will
        # be an absolute path as well. Example:
        # walk_dir = os.path.abspath(walk_dir)

        # print('walk_dir (absolute) = ' + os.path.abspath(walk_dir))

        for root, subdirs, files in os.walk(walk_dir):
            # print('--\nroot = ' + root)
            list_file_path = os.path.join(root, 'my-directory-list.txt')
            # print('list_file_path = ' + list_file_path)

            with open(list_file_path, 'wb') as list_file:
                # for subdir in subdirs:
                #    print('\t- subdirectory ' + subdir)

                for filename in files:
                    file_path = os.path.join(root, filename)

                    # print('\t- file %s (full path: %s)' % (filename, file_path))

                    FileList.append([])
                    FileList[len(FileList)-1].append(file_path)
                    FileList[len(FileList)-1].append(filename)

        self.prograssBar.minimum=0
        self.progressBar.maximum=len(FileList)-1

        for i in range(0,len(FileList)-1):
            self.ResultsList.addItem(FileList[i][0])
            self.progressBar.setValue(i)



if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())