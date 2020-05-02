#! /usr/bin/python3
 
import os, sys, time, datetime, hashlib, getopt
# import xml.etree.ElementTree as ET
from lxml import etree
#   So that we can use configuration files
import configparser
#   Use 'platform' library to identify OS.
import platform


#   GUI INCLUDES
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox

from PyQt5.QtCore import pyqtSignal

from AboutDialog import Ui_AboutDialog

#   Main screen code
from fdf_main import Ui_MainWindow
#   Dialog - to display progress
# from ProgressDialog import Ui_Dialog
from ProgressBar import ProgressDlg


VersionNumber="0.8"


#   HISTORY
#
#   0.1     Initial release - command line only
#   0.2     GUI release
#   0.3     Bugfixes:
#           Crash in BinaryChopSearch routine - cured.
#   0.4     Load and Save configurations to INI files
#   0.5     Add exception code to deal with invalid timestamps for files under windows
#   0.6     Added low-memory hash calculate option
#           Added force to GUI option rather than having to rename the python program.
#           As files are scanned, the output file is generated (including database file)
#   0.7     Progress bar now works again, also, progress bar now shows name of file being hashed and its size
#           Works the same in gui as console version.
#   0.8     Bug fix - error on deriving file name in linux environments.



#   ProcessBar dialog global communication variables...

#   Signal the window to close 0=keep open, 1=close
ProgressBar_CLOSE=0
ProgressBar_FILETOTAL=0
ProgressBar_TEXT=''
ProgressBar_PROGRESS_1=0
ProgressBar_Finished_Processing=0

UseLowMemory=0          # 0.6
ForceUseGUI=0           # 0.6
UseConfigFile=0
ConfigFileName=""
InputDirectory=[]
OutputFile='fdf_scanner_output'

#   Use a global time variable for output
#   Only update the screen if we've had more than 1 sec - otherwise we spend
#   lots of processing time updating the screen with every number.
GlobalTimer = time.time()


PreserveDir=[]
DatabaseFile=''

OLDFileDB = []
FileDB = []

MD5KeptCount=0
MD5CalculatedCount=0
DuplicatesCount=0

IsWindows=0
OutputFileRemark="# "
OutputFileRemove="rm "
OutputFileExtension=".sh"


def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(int(size)) +' '+ power_labels[n]+'b'



def BinaryChopSearch( SearchString ):
    global OLDFileDB

    LowPtr=0
    HighPtr=len(OLDFileDB)-1

    Ctr=0
    MidPtr=int((HighPtr-LowPtr)/2)

    try:
        while (not(OLDFileDB[LowPtr][1]==SearchString) and (MidPtr > 50)):

            MidPtr=int((HighPtr-LowPtr)/2)
            MidVal=OLDFileDB[LowPtr+MidPtr][1]

            if OLDFileDB[LowPtr+MidPtr][1] == SearchString:
                break

            if OLDFileDB[LowPtr+MidPtr][1] > SearchString:
                HighPtr=HighPtr-MidPtr
            else:
                LowPtr=LowPtr+MidPtr

            Ctr+=1

    except:
        pass


    if OLDFileDB[LowPtr+MidPtr][1] == SearchString:
        return (LowPtr+MidPtr)

    # Ok, look at the next 60...


    try:

        Ctr=0

        while (not(OLDFileDB[LowPtr+Ctr][1] == SearchString) and Ctr<60 and (LowPtr+Ctr)<len(FileDB)):
            MidVal = OLDFileDB[LowPtr + Ctr][1]
            Ctr+=1

        if OLDFileDB[LowPtr + Ctr][1] == SearchString:
            return (LowPtr+Ctr)
        else:
            return -1

    except:
        return -1


def ProgressBar( OutputText, TotalCount=0, CurrentCount=0, BarSize=40, TotalLineLength=80,ForceOutput=0):
    global GlobalTimer
    global ProgressBar_PROGRESS_1

    ProgressBar_PROGRESS_1=CurrentCount

    try:
        columns, rows = os.get_terminal_size(0)
    except OSError:
        try:
            columns, rows = os.get_terminal_size(1)
        except:
            columns=80
            rows=1

    # print ("TotalLineLength:"+str(TotalLineLength)+" rows:"+str(columns))

    if TotalLineLength > columns:
        TotalLineLength_Used=columns
    else:
        TotalLineLength_Used=TotalLineLength

    if (time.time() - GlobalTimer) > 1 or ForceOutput==1 :
        #   its been more than 1 sec since last output, so update the screen

        if TotalCount>0:
            #   We've got values - do a progressbar
            formatted_name = '\r '+ ( "=" * int(BarSize*(CurrentCount/TotalCount)))+( " " * (BarSize-int(40*(CurrentCount/TotalCount))))+' '+OutputText+(" " * 80)
            sys.stdout.write(formatted_name[0:TotalLineLength_Used])
            sys.stdout.flush()
            GlobalTimer = time.time()

        else:
            #   No values - simply output the text
            formatted_name = '\r ' + OutputText+(" " * 80)
            sys.stdout.write(formatted_name[0:TotalLineLength_Used])
            sys.stdout.flush()
            GlobalTimer = time.time()


#   Given a specific directory, scan and load the data into the FileDB list
def ScanDirectory(walk_dir):

    global ProgressBar_PROGRESS_1
    global ProgressBar_FILETOTAL
    global IsWindows
    global DuplicatesCount
    global DatabaseFile

    FileCount = 0

    #   Go through all the files, but dont follow links
    for root, subdirs, files in os.walk(walk_dir, followlinks=False):

        for filename in files:

            file_path = os.path.join(root, filename)

            #   Are we looking at a 'real' file?
            if os.path.isfile(file_path) and not os.path.islink(file_path):

                #   Yes - save the data
                FileCount = FileCount + 1

                ProgressBar_FILETOTAL=len(FileDB)

                if FileCount % 1000:
                    ProgressBar('FileCount ' + str(FileCount))

                #   Grab the modification time
                (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file_path)

                #   0) Filename
                #   1) File path + file name
                #   2) Modification time
                #   3) size
                #   4) MD5
                #   5) Perform delete

                #   And save the data into the array...
                #   If we're doing windows, switch everything to upper case, as windows isn't case sensitive
                if IsWindows==1:
                    Filepath=file_path.upper()
                    try:
                        timestamp = time.ctime(mtime)
                    except:
                        print("Timestamp is invalid for file {}".format(Filepath))
                        timestamp = 0
                    FileDB.append([filename.upper(), Filepath.replace('/','\\'), timestamp, size, '', 'N'])
                else:
                    FileDB.append([filename, file_path, time.ctime(mtime), size, '', 'N'])

#   Given a full filepath and filename - is this a file thats in the 'preserve' list?
def CheckPreserve(Fname):
    global IsWindows

    DoPreserve=0

    #   Loop through all the preserve data
    for PreservePath in PreserveDir:

        PPath=PreservePath

        if IsWindows==1:
            PPath=PPath.upper()

        #   If the filename like PreserveDir, mark the file as 'preserved'
        if Fname[:len(PPath)] == PPath:
            DoPreserve=1

    #   1=Yes, 0 =No
    return DoPreserve



def GetHistoricMD5(FullFileName,FileDate,FileSize):
    #   Check through the 'OLDFileDB' data - i.e. data from the XML database file specified in input params
    #   if we find the file (fullfilename+filedate+filesize) - return the MD5 - that way, we won't
    #   need to re-calculate it - and this will save a LOT of time... :-)

    #   0) Filename
    #   1) File path + file name
    #   2) Modification time
    #   3) size
    #   4) MD5
    FoundMD5=""

    Loc=-1

    if len(OLDFileDB)>0:
        Loc=BinaryChopSearch( FullFileName )

    #for sublist in OLDFileDB:
    #keys=[x for x in OLDFileDB if x[1] == FullFileName]
    #for sublist in keys:

    if Loc>=0:
        if OLDFileDB[Loc][1] == FullFileName and OLDFileDB[Loc][2] == FileDate and str(OLDFileDB[Loc][3]) == str(FileSize) :
            FoundMD5 = OLDFileDB[Loc][4]

    return FoundMD5

    
    
def OutputHelp():
    print('fdf_scanner.py -i <inputdir> [-i <inputdir>] [-p <preservedir>] [-p <preservedir>] [-c <configfile>] [-w] [-m] [-g] [-o <outputfile>]')
    print('')
    print('Where')
    print('  -i <InputDir>  (Mandatory) directory to scan for duplicates')
    print('  -p <PreserveDir> directory to NOT delete from')
    print('  -c <ConfigFile>  file holding run parameters')
    print('  -w               output file in WINDOWS Command prompt syntax (batch file)')
    print('  -m               use low memory footprint checksum calculation - slower')
    print('  -g               force to open as GUI')
    print('  -o <OutputFile>  put comments/deletions in specific file - default fdf_scanner_output.sh (or .bat)')


    
def ParseInputOpts(argv):
    #   Parse input options

    global UseConfigFile, ConfigFileName, InputDirectory, OutputFile, PreserveDir, DatabaseFile, OLDFileDB, FileDB
    global GlobalTimer
    global MD5KeptCount, MD5CalculatedCount, DuplicatesCount
    global IsWindows
    global OutputFileRemark, OutputFileRemove, OutputFileExtension
    global ForceUseGUI, UseLowMemory
    
    try:
        opts, args = getopt.getopt(argv[1:],"hi:o:p:d:c:wmg",["ifile=","ofile=","preservedir="])
    except getopt.GetoptError:
        print('no options given...')
        OutputHelp()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            OutputHelp()
            sys.exit()
        if opt in ("-w", "--windows"):
            OutputFileRemark = "REM "
            OutputFileRemove = "DEL "
            OutputFileExtension = ".BAT"
            IsWindows=1
        elif opt in ("-c", "--configfile"):
            #   Ok, we're using a config file rather than parameters from the command line
            UseConfigFile=1
            ConfigFileName=arg
        elif opt in ("-i", "--ifile"):
            if IsWindows == 1:
                #   Windows - switch to upper case as we're not case sensitive
                InputDirectory.append(arg.upper())
            else:
                InputDirectory.append(arg)
        elif opt in ("-o", "--ofile"):
            OutputFile = arg
        elif opt in ("-p", "--preservedir"):
            if IsWindows == 1:
                #   Windows - switch to upper case as we're not case sensitive
                PreserveDir.append(arg.upper())
            else:
                PreserveDir.append(arg)
        elif opt in ("-d", "--databasefile"):
            DatabaseFile = arg
        elif opt in ("-m", "--lomem"):
            print ("Force to use low memory")
            UseLowMemory = 1
        elif opt in ("-g", "--gui"):
            print("Force to GUI")
            ForceUseGUI = 1

    if ForceUseGUI==0 :

        if UseConfigFile==1:
            #   Ok, we're using a config file to pick up parameters:

            #   Create and open the config file
            config = configparser.ConfigParser()
            config.read(ConfigFileName)

            #   Loop through the input director(ies) and add then to the InputDirectory list.
            try:
                for x in config['InputDirectories']:
                    InputDirectory.append(config['InputDirectories'][x])
            except:
                pass

            #   Loop through the input director(ies) and add then to the InputDirectory list.
            try:
                for x in config['PreserveDirectories']:
                    PreserveDir.append(config['PreserveDirectories'][x])
            except:
                pass

            #   Loop through the input director(ies) and add then to the InputDirectory list.
            try:
                for x in config['OutputFile']:
                    OutputFile= (config['OutputFile'][x])
            except:
                pass

            #   Loop through the input director(ies) and add then to the InputDirectory list.
            try:
                for x in config['DatabaseFile']:
                    DatabaseFile=config['DatabaseFile'][x]
            except:
                pass

            #   Loop through the input director(ies) and add then to the InputDirectory list.
            try:
                for x in config['WindowsOutput']:
                    OutputFileRemark = "REM "
                    OutputFileRemove = "DEL "
                    OutputFileExtension = ".BAT"
            except:
                pass

        #   Now that we have the file name, put the correct extension onto it.
        OutputFile=OutputFile+OutputFileExtension


        if len(InputDirectory)==0:
            print('Error: at least ONE input directory is required')
            OutputHelp()
            sys.exit(-1)

        for Inputs in InputDirectory:
            print('Input directory:'+Inputs)
        print('Output file        '+OutputFile)
        for Preserves in PreserveDir:
            print('Preserve directory:'+Preserves)
        print('Database file      '+DatabaseFile)


    
def ReadDatabaseFile(DBFile):
    #   If a database file has been specified, open it and read into OLDFileDB...

    global OLDFileDB
    
    #   Database file is specified - read it in to a memory structure

    if os.path.isfile(DBFile):

        tree = etree.parse(DBFile)
        root = tree.getroot()

        for child in root:

            MD5Val = child.find('MD5')
            if MD5Val is None:
                MD5ValText= ""
            else:
                MD5ValText = child.find('MD5').text

            OLDFileDB.append([child.find('filename').text,
                              child.find('fullfilename').text,
                              child.find('modtime').text,
                              child.find('size').text,
                              MD5ValText])

        # Now that we've read in - ensure the list is sorted...
        OLDFileDB.sort(key=lambda x: x[1])

#   0.6     Rather than using normal SHA256, which reads the entire file into memory
#           this procedure reads the file blocks and calculates the hashes from that
#           thereby using less memory.
def file_hash(filename):
    h = hashlib.sha256()
    with open(filename, 'rb', buffering=0) as f:
        for b in iter(lambda : f.read(128*1024), b''):
            h.update(b)
    return h.hexdigest()

 
def CalculateHashes():
    #   Get MD5 values for files if there's more than one file of exactly the same size...

    global UseConfigFile, ConfigFileName, InputDirectory, OutputFile, PreserveDir, DatabaseFile, OLDFileDB, FileDB
    global GlobalTimer
    global MD5KeptCount, MD5CalculatedCount, DuplicatesCount
    global IsWindows
    global OutputFileRemark, OutputFileRemove, OutputFileExtension
    global ProgressBar_TEXT

    global ProgressBar_PROGRESS_1

    print("Sorting...")

    #    Sort the file information to make it easier to process.
    FileDB.sort(key=lambda x: x[3])

    #print("")
    #print("Calculating hashes")

    # Keep a count of files processed - as we generate hashes, save every so often.
    FileDelta=0

    print ("Matching...")

    # Preserve the value of ProgressBar_TEXT so we can restore when finished
    Saved_ProgressBar_TEXT=ProgressBar_TEXT


    for i in range(1,len(FileDB)-1):

        ProgressBar('Matching files ' + str(i),TotalCount=(len(FileDB)-1),CurrentCount=i),
            
        if FileDB[i][3] == FileDB[i+1][3] or FileDB[i][3] == FileDB[i-1][3]:
            try:

                MD5Val=""

                if len(DatabaseFile) > 0:
                    #   Filename, date, size
                    MD5Val=GetHistoricMD5(FileDB[i][1], FileDB[i][2], FileDB[i][3])

                if len(FileDB[i][4]) > 0:
                    # We've already worked out a hash
                    MD5Val=FileDB[i][4]

                if len(MD5Val)>0:
                    #   Got an MD5 from historic data:
                    FileDB[i][4] = MD5Val
                    MD5KeptCount+=1
                else:
                    #   No historic match - re-calculate
                    # print("Calculating hash:"+FileDB[i][1])

                    if OS[0:5] == 'Linux':
                        Fname = FileDB[i][1].rsplit("/", 1)[1]
                    else:
                        Fname = FileDB[i][1].rsplit("\\", 1)[1]

                    Fsize = format_bytes(FileDB[i][3])

                    ProgressBar('Matching files ' + str(i)+ ' checking:'+Fname+" ("+Fsize+")", TotalCount=(len(FileDB) - 1), CurrentCount=i ,ForceOutput=1, TotalLineLength=200)
                    ProgressBar_TEXT = Saved_ProgressBar_TEXT + chr(13) + chr(10) + "    Examining files..."+ chr(13) + chr(10)+'           checking:'+Fname+" ("+Fsize+")"
                    try:
                        #   Is the size too large to fit into memory? (250Mb)
                        if FileDB[i][3] > (1024 * 1024 * 250):
                            FileDB[i][4] = file_hash(FileDB[i][1])
                        else:
                            FileDB[i][4] = hashlib.sha256(open(FileDB[i][1], 'rb').read()).hexdigest()
                        MD5CalculatedCount+=1
                    except:
                        print('Error (sha256:nomatch):'+FileDB[i][1])  #+' '+sys.exc_info()[0]
                        FileDB[i][4] = "OSERROR"

                    # 0.7 - if we've processed more than 'x' save values.
                    FileDelta = FileDelta + 1

                    if FileDelta > 100:
                        FileDelta = 0

                        ProgressBar_TEXT = Saved_ProgressBar_TEXT + chr(13) + chr(10) + "    Examining files..." + chr(13) + chr(10) + '           saving...'
                        ProgressBar('Matching files ' + str(i) + ' saving... ',
                                    TotalCount=(len(FileDB) - 1), CurrentCount=i, ForceOutput=1, TotalLineLength=200)

                        # We've added x files - do a quick process and save.

                        #    Locate duplicate files
                        # ProgressBar_TEXT = ProgressBar_TEXT+chr(13) + chr(10) +"    Locating duplicates..."
                        # QApplication.processEvents()
                        LocateDups()

                        #    Generate the output
                        # ProgressBar_TEXT = ProgressBar_TEXT+chr(13) + chr(10) +"    Generating output file..."
                        # QApplication.processEvents()
                        DuplicatesCount = 0
                        GenerateOutput()

                        #    If we've got a database file name, save it
                        if len(DatabaseFile) > 0:
                            SaveDatabase()

            except OSError:
                FileDB[i][4] = "OSERROR"

    # restore ProgressBar_TEXT
    ProgressBar_TEXT=Saved_ProgressBar_TEXT


def LocateDups():

    global UseConfigFile, ConfigFileName, InputDirectory, OutputFile, PreserveDir, DatabaseFile, OLDFileDB, FileDB
    global GlobalTimer
    global MD5KeptCount, MD5CalculatedCount, DuplicatesCount
    global IsWindows
    global OutputFileRemark, OutputFileRemove, OutputFileExtension
    
    # re-sort on Size, md5sum then fullpath+filename - largest first
    FileDB.sort(key=lambda x: (x[3], x[4], x[1]),reverse=True)

    i=1

    while i < len(FileDB)-1:
    # for i in range(1,len(FileDB)-1):

        #   Have we got a MD5 match?
        if (FileDB[i][4] == FileDB[i + 1][4] or FileDB[i][4] == FileDB[i - 1][4]) and len(FileDB[i][4]) > 0:

            This_MD5=FileDB[i][4]

            #   Get range of same MD5
            StartPtr = i
            EndPtr = i

            try:
                while FileDB[EndPtr + 1][4] == This_MD5 and EndPtr < len(FileDB)-2:
                    EndPtr += 1
            except:
                print("Error located in locatedup")
            #   Start and End now mark the start and end of THIS md5.

            #   Count of preserved files.
            PreserveCount=0

            #   Preserve files if they exist within 'PreserveDir' option
            for ptr in range(StartPtr,EndPtr+1):


                #   If the filename like PreserveDir, mark the file as 'preserved'
                #   We may have many 'preserveDirs' use a function that returns 1
                #   if we need to preserve.
                if CheckPreserve(FileDB[ptr][1]) == 1:

                    #   Yes: mark the file as preserved
                    FileDB[ptr][5] = 'X'

                    #   And mark the count of files preserved.
                    PreserveCount+=1

            #   Now mark all the records - if PreserveCount=0, don't mark the first entry
            for ptr in range(StartPtr, EndPtr+1):

                if PreserveCount==0 and ptr==StartPtr:
                    #   There's no preserved, and we're looking at the first - mark it keep
                    FileDB[ptr][5] = 'K'
                elif FileDB[ptr][5]!='X':
                    #   We've got preserved , and this isn't one to mark preserve.
                    FileDB[ptr][5] = 'Y'

            #   We've now processed until 'EndPtr'

            i=EndPtr

        #   End if

        i+=1


        
def GenerateOutput():
    global UseConfigFile, ConfigFileName, InputDirectory, OutputFile, PreserveDir, DatabaseFile, OLDFileDB, FileDB
    global GlobalTimer
    global MD5KeptCount, MD5CalculatedCount, DuplicatesCount
    global IsWindows
    global OutputFileRemark, OutputFileRemove, OutputFileExtension
    
    OutFile = open(OutputFile, 'w')

    Last_MD5='xXxXxX'

    for i in range(1, len(FileDB) - 1):

        if FileDB[i][5] == 'Y':
            if Last_MD5 != FileDB[i][4] and len(FileDB[i][4]) > 0:
                OutFile.write('\n')

            OutFile.write('\n'+OutputFileRemark+'    (' + FileDB[i][4] + ') ' + FileDB[i][1] + ' Size:' + str(FileDB[i][3]))
            OutFile.write('\n'+OutputFileRemove+' "' + FileDB[i][1]+'"')

            DuplicatesCount+=1

            Last_MD5 = FileDB[i][4]

        elif FileDB[i][5] == 'X':
            if Last_MD5 != FileDB[i][4] and len(FileDB[i][4]) > 0:
                OutFile.write('\n')

            OutFile.write('\n'+OutputFileRemark+'    (' + FileDB[i][4] + ') ' + FileDB[i][1] + ' Size:' + str(FileDB[i][3]))
            OutFile.write('\n'+OutputFileRemark+' PRESERVE "' + FileDB[i][1] + '"')

            Last_MD5 = FileDB[i][4]

        elif FileDB[i][5] == 'K':
            if Last_MD5 != FileDB[i][4] and len(FileDB[i][4]) > 0:
                OutFile.write('\n')

            OutFile.write('\n'+OutputFileRemark+'    (' + FileDB[i][4] + ') ' + FileDB[i][1] + ' SAVE Size:' + str(FileDB[i][3]))
            OutFile.write('\n'+OutputFileRemark+' KEEP "' + FileDB[i][1]+ '"')

            Last_MD5 = FileDB[i][4]

    OutFile.close()


def SaveDatabase():
    global UseConfigFile, ConfigFileName, InputDirectory, OutputFile, PreserveDir, DatabaseFile, OLDFileDB, FileDB
    global GlobalTimer
    global MD5KeptCount, MD5CalculatedCount, DuplicatesCount
    global IsWindows
    global OutputFileRemark, OutputFileRemove, OutputFileExtension

    #   Save the database
    root = etree.Element("root")

    for i in range(1, len(FileDB) - 1):

        #   Only back up if we've got file > 250 bytes, and we've got a hash to save
        if FileDB[i][3] > 250 and len(FileDB[i][4])>0:

            #   0) Filename
            #   1) File path + file name
            #   2) Modification time
            #   3) size
            #   4) MD5

            doc = etree.SubElement(root, "file")

            # doc = ET.SubElement(root, "file")

            etree.SubElement(doc, "filename").text = FileDB[i][0]
            etree.SubElement(doc, "fullfilename").text = FileDB[i][1]
            etree.SubElement(doc, "modtime").text = FileDB[i][2]
            etree.SubElement(doc, "size").text = str(FileDB[i][3])
            etree.SubElement(doc, "MD5").text = FileDB[i][4]


    tree = etree.ElementTree(root)
    tree.write(DatabaseFile,pretty_print=True)



class AboutDialog(QtWidgets.QDialog, Ui_AboutDialog):
    CloseClicked = 0


    def __init__(self, desc=None, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)
        self.VersionText.setText(" By Carl Beech - V"+VersionNumber+" 2020"+chr(13)+chr(10)+"http://github.com/carlbeech/fast-duplicate-finder/"+chr(13)+chr(10)+chr(13)+chr(10)+"Locate duplicate files and do it fast!")
        self.ProgramText.setText("fdf_scanner")


#   ***********************************************************************
#   DeDupWorker - a separate thread which performs the main work of
#                   de-dup - essentially calling the same routines as the
#                   command line version, but with feedback to the GUI...


class DeDupWorker(QtCore.QThread):
    sec_signal = pyqtSignal(str)
    def __init__(self, parent=None):
        super(DeDupWorker, self).__init__(parent)
        self.current_time = 0
        self.go = True
    def run(self):

        global UseConfigFile, ConfigFileName, InputDirectory, OutputFile, PreserveDir, DatabaseFile, OLDFileDB, FileDB
        global GlobalTimer
        global MD5KeptCount, MD5CalculatedCount, DuplicatesCount
        global IsWindows
        global OutputFileRemark, OutputFileRemove, OutputFileExtension
        global app

        global ProgressBar_CLOSE
        global ProgressBar_FILETOTAL
        global ProgressBar_TEXT
        global ProgressBar_PROGRESS_1
        global ProgressBar_Finished_Processing

        ProgressBar_CLOSE=0
        ProgressBar_Finished_Processing=0

        #this is a special fxn that's called with the start() fxn
        # Old database file to read in?
        if len(DatabaseFile) > 0:
            # pb.setValue(((i + 1) / 100) * 100)
            ProgressBar_TEXT=ProgressBar_TEXT+chr(13)+chr(10)+"    Read database file..."
            # QApplication.processEvents()

            # ProgressDialogUi.ProgressText.setText(ProgressDialogUi.ProgressText.text()+chr(10)+chr(13)+"   Read database file...")

            ReadDatabaseFile(DatabaseFile)

        ProgressBar_TEXT = ProgressBar_TEXT+chr(13) + chr(10) +"    Get input directories..."
        # QApplication.processEvents()

        # Read input director(ies) into InputDirectory list, and scan all files in from each..
        for Inputs in InputDirectory:
            print('Input directory:' + Inputs)
            ScanDirectory(Inputs)
            print("")

        #   Output total files to the progress dialog.
        ProgressBar_FILETOTAL=(len(FileDB))

        #    Calculate hash values for all files.
        ProgressBar_TEXT = ProgressBar_TEXT+chr(13) + chr(10) +"    Examining files..."
        #QApplication.processEvents()
        CalculateHashes()

        #    Locate duplicate files
        ProgressBar_TEXT = ProgressBar_TEXT+chr(13) + chr(10) +"    Locating duplicates..."
        # QApplication.processEvents()
        LocateDups()

        #    Generate the output
        ProgressBar_TEXT = ProgressBar_TEXT+chr(13) + chr(10) +"    Generating output file..."
        # QApplication.processEvents()
        GenerateOutput()

        #    If we've got a database file name, save it
        if len(DatabaseFile) > 0:
            ProgressBar_TEXT = ProgressBar_TEXT+chr(13) + chr(10) +"    Save database file..."
            #QApplication.processEvents()
            SaveDatabase()

        ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + "    Complete."

        ProgressBar_Finished_Processing=1



#   GUI Extra Support Procedures    =====================================================================

#   Dialog boxes for getting files and directories
def GetFile(self):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName = QFileDialog.getSaveFileName(self, 'Open file', '.', 'OpenFile(*)')
    if fileName:
        # self.Databasefile.setText(fileName[0])
        #   If Windows, change the separator
        FName = fileName[0]
        if os.sep == '\\':
            FName = FName.replace('/', '\\')
        return FName
    else:
        return ""

#   Dialog boxes for getting files and directories
def OpenFile(self):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName = QFileDialog.getOpenFileName(self, 'Open file', '.', 'OpenFile(*)')
    if fileName:
        # self.Databasefile.setText(fileName[0])
        #   If Windows, change the separator
        FName = fileName[0]
        if os.sep == '\\':
            FName = FName.replace('/', '\\')
        return FName
    else:
        return ""



def GetDir(self):
    options = QFileDialog.Options()
    # options |= QFileDialog.DontUseNativeDialog
    fileName = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
    if fileName:
        # self.Databasefile.setText(fileName[0])

        #   If Windows, change the separator
        if os.sep=='\\':
            fileName=fileName.replace('/', '\\')
        return fileName
    else:
        return ""


#   *****************************************************************************
#   Main UI window

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

        self.actionAbout.triggered.connect(self.AboutBox)

        #   Connect execute button
        self.StartProcessing.clicked.connect(self.PerformDeDup)

        #   Menu: Load configuration
        self.actionLoad_Configuration.triggered.connect(self.LoadConfig)

        #   Menu: Save configuration
        self.actionSave_Configuration.triggered.connect(self.SaveConfig)

        #   Holder for about dialog window
        self.Ui_AboutDialog=None

        #   Holder for progressbar dialog window
        self.pb=None


    def LoadConfig(self):

        #   Clear out on-screen configuration and load a configuration from file.

        #   Start with clearing on-screen data...

        self.SearchDirectoryList.clear()
        self.PreserveDirectoryList.clear()
        self.Databasefile.setText("")
        self.Configurationfile.setText("")
        self.Outputscript.setText("")

        #   Now, load a configuration file...

        #   File dialog to get file name
        lfile = ""
        lfile = OpenFile(self)

        config = configparser.ConfigParser()
        config.read(lfile)

        #   Loop through the input director(ies) and add then to the Search list.
        try:
            for x in config['InputDirectories']:
                self.SearchDirectoryList.addItem(config['InputDirectories'][x])
        except:
            pass

        # Loop through the input director(ies) and add then to the Preserve list.
        try:
            for x in config['PreserveDirectories']:
                self.PreserveDirectoryList.addItem(config['PreserveDirectories'][x])
        except:
            pass

        # Loop through the input director(ies) and add then to the InputDirectory list.
        try:
            for x in config['OutputFile']:
                self.Outputscript.setText(config['OutputFile'][x])
        except:
            pass

        # Loop through the input director(ies) and add then to the InputDirectory list.
        try:
            for x in config['DatabaseFile']:
                self.Databasefile.setText(config['DatabaseFile'][x])
        except:
            pass

    def SaveConfig(self):

        #   Ask for a configuration file name and save on-screen data as a configuration file.
        sfile = ""
        sfile = GetFile(self)

        if sfile:

            OutFile = open(sfile, 'w')

            if self.SearchDirectoryList.count()>0:
                OutFile.write('\n[InputDirectories]\n')

                i=0
                while i <= self.SearchDirectoryList.count()-1:
                    OutFile.write('InputDirectory'+str(i)+'='+self.SearchDirectoryList.item(i).text()+'\n')
                    i+=1

            if self.PreserveDirectoryList.count() > 0:
                OutFile.write('\n[PreserveDirectories]\n')

                i=0
                while i <= self.PreserveDirectoryList.count()-1:
                    OutFile.write('PreserveDirectory' + str(i) + '=' + self.PreserveDirectoryList.item(i).text() + '\n')
                    i+=1

            if len(self.Outputscript.text())>0:
                OutFile.write('\n[OutputFile]\n')
                OutFile.write('\nOutputFileName='+self.Outputscript.text()+'\n')

            if len(self.Databasefile.text())>0:
                OutFile.write('\n[DatabaseFile]\n')
                OutFile.write('\nDatabaseFileName='+self.Databasefile.text()+'\n')

            OutFile.close()

    def AboutBox(self):

        if not self.Ui_AboutDialog:
            self.Ui_AboutDialog = AboutDialog()
        if self.Ui_AboutDialog.isVisible():
            print('Hiding')
            self.Ui_AboutDialog.hide()
            # hide or close, it's your choice
            # self.sisterWin.close()
        else:
            print('Showing')
            self.Ui_AboutDialog.show()


        # print("aboutbox")
        # AB = AboutDialog()
        # AB.show()

    def DBFileDialog(self):

        tfile = ""
        tfile = GetFile(self)
        if len(tfile) > 0:
            self.Databasefile.setText(tfile)

    def ConfFileDialog(self):

        tfile = ""
        tfile = GetFile(self)
        if len(tfile) > 0:
            self.Configurationfile.setText(tfile)

    def OutputFileDialog(self):

        tfile = ""
        tfile = GetFile(self)
        if len(tfile) > 0:
            self.Outputscript.setText(tfile)

    def AddSearchDirectory(self):
        tfile = ""
        tfile = GetDir(self)
        if len(tfile) > 0:
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

    def PerformDeDup(self):
        global UseConfigFile, ConfigFileName, InputDirectory, OutputFile, PreserveDir, DatabaseFile, OLDFileDB, FileDB
        global GlobalTimer
        global MD5KeptCount, MD5CalculatedCount, DuplicatesCount
        global IsWindows
        global OutputFileRemark, OutputFileRemove, OutputFileExtension
        global app

        global ProgressBar_CLOSE
        global ProgressBar_FILETOTAL
        global ProgressBar_TEXT
        global ProgressBar_PROGRESS_1
        global ProgressBar_Finished_Processing

        OutputFile = 'fdf_scanner_output'

        ProgressBar_TEXT=""

        StartTime = time.time()

        #   Clear out the arrays.
        del FileDB[:]
        del OLDFileDB[:]
        del InputDirectory[:]
        del PreserveDir[:]

        #   Put the values from the GUI into the fdf_scanner input variables.

        if self.SearchDirectoryList.count()==0:
            #   No search directories specified  - error
            print("error - no search directories specified")

        OS = platform.platform()

        if OS[0:5] == 'Linux':
            print("Linux OS detected")
            OutputFileRemark = "# "
            OutputFileRemove = "rm "
            OutputFileExtension = ".sh"
            IsWindows=0
        elif OS[0:7] == 'Windows':
            print("Windows OS detected")
            OutputFileRemark = "REM "
            OutputFileRemove = "DEL "
            OutputFileExtension = ".BAT"
            IsWindows=1
        else:
            print("Unknown OS?")
        print("")

        for index in range(self.SearchDirectoryList.count()):

            item= self.SearchDirectoryList.item(index)

            if IsWindows == 1:
                #   Windows - switch to upper case as we're not case sensitive
                InputDirectory.append(item.text().upper())
            else:
                InputDirectory.append(item.text())

        for index in range(self.PreserveDirectoryList.count()):

            item= self.PreserveDirectoryList.item(index)

            if IsWindows == 1:
                #   Windows - switch to upper case as we're not case sensitive
                PreserveDir.append(item.text().upper())
            else:
                PreserveDir.append(item.text())


        if len(self.Outputscript.text())>0:
            OutputFile=self.Outputscript.text()

        if len(self.Databasefile.text()) > 0:
            DatabaseFile = self.Databasefile.text()

        if len(self.Configurationfile.text()) > 0:
            ConfigFileName = self.Configurationfile.text()
            UseConfigFile = 1


        if UseConfigFile == 1:
            #   Ok, we're using a config file to pick up parameters:

            #   Create and open the config file
            config = configparser.ConfigParser()
            config.read(ConfigFileName)

            #   Loop through the input director(ies) and add then to the InputDirectory list.
            try:
                for x in config['InputDirectories']:
                    InputDirectory.append(config['InputDirectories'][x])
            except:
                pass

            # Loop through the input director(ies) and add then to the InputDirectory list.
            try:
                for x in config['PreserveDirectories']:
                    PreserveDir.append(config['PreserveDirectories'][x])
            except:
                pass

            # Loop through the input director(ies) and add then to the InputDirectory list.
            try:
                for x in config['OutputFile']:
                    OutputFile = (config['OutputFile'][x])
            except:
                pass

            # Loop through the input director(ies) and add then to the InputDirectory list.
            try:
                for x in config['DatabaseFile']:
                    DatabaseFile = config['DatabaseFile'][x]
            except:
                pass

            # Loop through the input director(ies) and add then to the InputDirectory list.
            try:
                for x in config['WindowsOutput']:
                    OutputFileRemark = "REM "
                    OutputFileRemove = "DEL "
                    OutputFileExtension = ".BAT"
            except:
                pass

        # Now that we have the file name, put the correct extension onto it.
        OutputFile = OutputFile + OutputFileExtension

        #   Now we've grabbed the input parameters - start to process...=====================================

        #   Set up communication variables.
        ProgressBar_CLOSE=0
        ProgressBar_FILETOTAL=0
        ProgressBar_PROGRESS_1=0
        ProgressBar_Finished_Processing=0
        # print("Starting DeDupWorker()")

        #   Open the progress dialog to keep the user updated with progress...
        self.pb = ProgressDlg(ProgressBar_CLOSE)

        #   Ensure the progressbar is at zero...
        self.pb.setValue(0)
        self.pb.show()

        #   Hive off the main processing into a separate thread so that the GUI
        #   can remain responsive.
        self.DeDupWorker = DeDupWorker()
        self.DeDupWorker.sec_signal.connect(self.label.setText)
        self.DeDupWorker.start()

        #   While the main thread is working, update the progress dialog.

        #   While the DeDupworker process is running, it variable has the value 0 and 1=finished.
        while(ProgressBar_Finished_Processing<2):

            #   Update the data on screen
            self.pb.setProgressText(ProgressBar_TEXT)
            self.pb.setTotalFiles(str(ProgressBar_FILETOTAL))

            #   If we've read in all the files, and now we can work out a % complete
            #   for the matching...
            if ProgressBar_FILETOTAL>0 and len(FileDB)>0:
                self.pb.setValue(100*(ProgressBar_PROGRESS_1/len(FileDB)))

            #   Let the system process any GUI updates...
            QApplication.processEvents()

            #   We don't need a tight-loop here...
            time.sleep(0.1)
            # print("in loop ")

            #   Have we got the signal that the worker has finished, and we can output stats?
            if ProgressBar_Finished_Processing==1:
                EndTime = time.time()

                ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + "Finished"
                ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + "Stats:"
                ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + "  Total files scanned:" + str(len(FileDB))
                # ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + "  Potential duplicates (filesizes the same):" + str(MD5CalculatedCount + MD5KeptCount)
                ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + "  Calculated SHA256 for files:" + str(MD5CalculatedCount)
                # ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + "  Count of SHA256 calculations saved due to database:" + str(MD5KeptCount)
                ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + ""
                ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + "  Total duplicates found:" + str(DuplicatesCount)
                ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + ""
                ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + "Started:" + datetime.datetime.fromtimestamp(StartTime).strftime('%Y-%m-%d %H:%M:%S')
                ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + "Finished:" + datetime.datetime.fromtimestamp(EndTime).strftime('%Y-%m-%d %H:%M:%S')
                ProgressBar_TEXT = ProgressBar_TEXT + chr(13) + chr(10) + "Total secs:" + str(int(EndTime - StartTime))
                self.pb.setProgressText(ProgressBar_TEXT)
                #   Ok, now we've output them - don't keep outputting them...
                ProgressBar_Finished_Processing=2

        #   When this procedure closes, it'll also close and tidy the DeDupWorker thread too...



#   MAIN CODE   =================================================================================

ProgramName=sys.argv[0]
ProgramName=ProgramName.upper()

#    Parse the arguments
ParseInputOpts(sys.argv)

#   Are we running in command line or GUI varsion?
#
#    if sys.argv[1]=='fdf_scanner'    ?
if ForceUseGUI==0 and (ProgramName[-14:]=='FDF_SCANNER.PY' or ProgramName[-11:]=='FDF_SCANNER' or ProgramName[-15:]=='FDF_SCANNER.EXE'):

    #    Running from the command line with arguments...

    print("Command line version (copy/rename fdf_scanner.py to fdf_scanner_gui.py or use -g param for GUI)")
    print("FDF_SCANNER By Carl Beech - V"+VersionNumber+" 2020")

    StartTime=time.time()

    OS = platform.platform()

    if OS[0:5]=='Linux':
        print("Linux OS detected")
        OutputFileRemark = "# "
        OutputFileRemove = "rm "
        OutputFileExtension = ".sh"
        IsWindows=0
    elif OS[0:7]=='Windows':
        print("Windows OS detected")
        OutputFileRemark = "REM "
        OutputFileRemove = "DEL "
        OutputFileExtension = ".BAT"
        IsWindows=1
    else:
        print("Unknown OS?")
    print("")

    #    Old database file to read in?
    if len(DatabaseFile) > 0:
        ReadDatabaseFile(DatabaseFile)

    #   Read input director(ies) into InputDirectory list, and scan all files in from each..
    print(" ")
    print("Reading input directorie(s)")
    print("")
    for Inputs in InputDirectory:
        print('Input directory:'+Inputs)
        ScanDirectory(Inputs)
        print("")

    print('Total files:'+str(len(FileDB)))

    #    Calculate hash values for all files.
    CalculateHashes()

    #    Locate duplicate files
    LocateDups()

    #    Generate the output
    DuplicatesCount=0
    GenerateOutput()

    #    If we've got a database file name, save it
    if len(DatabaseFile)>0:
        SaveDatabase()

    EndTime=time.time()

    #    Finally, print out stats.
    print("Finished")
    print("Stats:")
    print("  Total files scanned:"+str(len(FileDB)))
    # print("  Potential duplicates (filesizes the same):"+str(MD5CalculatedCount+MD5KeptCount))
    print("  Calculated SHA256 for files:"+str(MD5CalculatedCount))
    # print("  Count of SHA256 calculations saved due to database:"+str(MD5KeptCount))
    print("")
    print("  Total duplicates found:"+str(DuplicatesCount))
    print("")
    print("Started:"+datetime.datetime.fromtimestamp(StartTime).strftime('%Y-%m-%d %H:%M:%S'))
    print("Finished:"+datetime.datetime.fromtimestamp(EndTime).strftime('%Y-%m-%d %H:%M:%S'))
    print("Total secs:"+str(int(EndTime-StartTime)))

#   If we're running in the GUI then set up and open the GUI...
if ForceUseGUI==1 or (ProgramName[-18:]=='FDF_SCANNER_GUI.PY' or ProgramName[-15:]=='FDF_SCANNER_GUI' or ProgramName[-19:]=='FDF_SCANNER_GUI.EXE'):

    #    Running from the command line with arguments...

    print("GUI version (use fdf_scanner for command line)")

    if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        w = MainWindow()
        w.show()
        sys.exit(app.exec_())