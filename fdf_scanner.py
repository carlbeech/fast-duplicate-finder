#! /usr/bin/python3
 
import os, sys, time, hashlib, getopt
# import xml.etree.ElementTree as ET
from lxml import etree
#   So that we can use configuration files
import configparser

UseConfigFile=0
ConfigFileName=""
InputDirectory=[]
OutputFile='scanner_output.sh'

PreserveDir=[]
DatabaseFile=''

OLDFileDB = []
FileDB = []

MD5KeptCount=0
MD5CalculatedCount=0
DuplicatesCount=0


#   Given a specific directory, scan and load the data into the FileDB list
def ScanDirectory(walk_dir):

    FileCount = 0

    #   Go through all the files, but dont follow links
    for root, subdirs, files in os.walk(walk_dir, followlinks=False):

        for filename in files:

            file_path = os.path.join(root, filename)

            #   Are we looking at a 'real' file?
            if os.path.isfile(file_path) and not os.path.islink(file_path):

                #   Yes - save the data
                FileCount = FileCount + 1

                if FileCount % 1000:
                    formatted_name = '\r - FileCount ' + str(FileCount)
                    sys.stdout.write(formatted_name[0:80])
                    sys.stdout.flush()

                #   Grab the modification time
                (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file_path)

                #   0) Filename
                #   1) File path + file name
                #   2) Modification time
                #   3) size
                #   4) MD5
                #   5) Perform delete

                #   And save the data into the array...
                FileDB.append([filename, file_path, time.ctime(mtime), size, '', 'N'])



#   Given a full filepath and filename - is this a file thats in the 'preserve' list?
def CheckPreserve(Fname):

    DoPreserve=0

    #   Loop through all the preserve data
    for PreservePath in PreserveDir:

        #   If the filename like PreserveDir, mark the file as 'preserved'
        if Fname[:len(PreservePath)] == PreservePath:
            DoPreserve=1

    #   1=Yes, 0 =No
    return DoPreserve


#   Check through the 'OLDFileDB' data - i.e. data from the XML database file specified in input params
#   if we find the file (fullfilename+filedate+filesize) - return the MD5 - that way, we won't
#   need to re-calculate it - and this will save a LOT of time... :-)

#   0) Filename
#   1) File path + file name
#   2) Modification time
#   3) size
#   4) MD5
def GetHistoricMD5(FullFileName,FileDate,FileSize):

    FoundMD5=""


    for sublist in OLDFileDB:

        #print("")
        #print(">"+FullFileName+"< >"+FileDate+"< >"+str(FileSize)+"<   = ?")
        #print(">"+sublist[1]+"< >"+sublist[2]+"< >"+str(sublist[3])+"<   = ?")

        if sublist[1] == FullFileName and sublist[2] == FileDate and str(sublist[3]) == str(FileSize) :
            FoundMD5 = sublist[4]

            break

    return FoundMD5


#   Parse input options

try:
    opts, args = getopt.getopt(sys.argv[1:],"hi:o:p:d:c:",["ifile=","ofile=","preservedir="])
except getopt.GetoptError:
    print('scanner.py -i <inputdir> [-i <inputdir>] [-p <preservedir>] [-p preservedir] [-d <databaseSavefile>] [-o <outputfile>]')
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print('scanner.py -i <inputdir> [-i <inputdir>] [-p <preservedir>] [-p preservedir] [-d <databaseSavefile>] [-o <outputfile>]')
        sys.exit()
    elif opt in ("-c", "--configfile"):
        #   Ok, we're using a config file rather than parameters from the command line
        UseConfigFile=1
        ConfigFileName=arg
    elif opt in ("-i", "--ifile"):
        InputDirectory.append(arg)
    elif opt in ("-o", "--ofile"):
        OutputFile = arg
    elif opt in ("-p", "--preservedir"):
        PreserveDir.append(arg)
    elif opt in ("-d", "--databasefile"):
        DatabaseFile = arg


if UseConfigFile==1:
    #   Ok, we're using a config file to pick up parameters:

    #   Create and open the config file
    config = configparser.ConfigParser()
    config.read(ConfigFileName)

    #   Loop through the input director(ies) and add then to the InputDirectory list.
    for x in config['InputDirectories']:
        InputDirectory.append(config['InputDirectories'][x])

    #   Loop through the input director(ies) and add then to the InputDirectory list.
    for x in config['PreserveDirectories']:
        PreserveDir.append(config['PreserveDirectories'][x])

    #   Loop through the input director(ies) and add then to the InputDirectory list.
    for x in config['OutputFile']:
        OutputFile= (config['OutputFile'][x])

    #   Loop through the input director(ies) and add then to the InputDirectory list.
    for x in config['DatabaseFile']:
        DatabaseFile=config['DatabaseFile'][x]


if len(InputDirectory)==0:
    print('Error: at least ONE input directory is required (use -h for help)')
    exit(-1)

for Inputs in InputDirectory:
    print('Input directory:'+Inputs)
print('Output file        '+OutputFile)
for Preserves in PreserveDir:
    print('Preserve directory:'+Preserves)
print('Database file      '+DatabaseFile)


#   If a database file has been specified, open it and read into OLDFileDB...

if len(DatabaseFile) > 0:
    #   Database file is specified - read it in to a memory structure

    if os.path.isfile(DatabaseFile):

        tree = etree.parse(DatabaseFile)
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


#   Read input director(ies) into InputDirectory list, and scan all files in from each..

for Inputs in InputDirectory:
    print('Input directory:'+Inputs)
    ScanDirectory(Inputs)
    print("")

print('Total files:'+str(len(FileDB)))

FileDB.sort(key=lambda x: x[3])
 


#   Get MD5 values for files if there's more than one file of exactly the same size...

for i in range(1,len(FileDB)-1):

    if i % 1000:
        formatted_name = '\r - Matching files ' + str(i)
        sys.stdout.write(formatted_name[0:80])
        sys.stdout.flush()

    # print(FileDB[i][1] + "(" + str(FileDB[i][3]) + ")=" + FileDB[i + 1][1] + "(" + str(FileDB[i + 1][3]) + ")")
 
    if FileDB[i][3] == FileDB[i+1][3] or FileDB[i][3] == FileDB[i-1][3]:
        try:
            #formatted_name = '\r - get MD5: ' + FileDB[i][1] + (' ' * 90)

            #sys.stdout.write(formatted_name[0:100])
            #sys.stdout.flush()

            MD5Val=""

            if len(DatabaseFile) > 0:
                #   Filename, date, size
                MD5Val=GetHistoricMD5(FileDB[i][1], FileDB[i][2], FileDB[i][3])

            if MD5Val is None:
                # FileDB[i][4] = hashlib.md5(open(FileDB[i][1], 'rb').read()).hexdigest()
                FileDB[i][4] = hashlib.sha256(open(FileDB[i][1], 'rb').read()).hexdigest()
                MD5CalculatedCount+=1
            else:
                if len(MD5Val)>0:
                    #   Got an MD5 from historic data:
                    FileDB[i][4] = MD5Val
                    MD5KeptCount+=1
                else:
                    #   No historic match - re-calculate
                    FileDB[i][4] = hashlib.sha256(open(FileDB[i][1], 'rb').read()).hexdigest()
                    MD5CalculatedCount+=1

        except OSError:
            FileDB[i][4] = "OSERROR"

print("")

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

        while FileDB[EndPtr + 1][4] == This_MD5:
            EndPtr += 1

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


OutFile = open(OutputFile, 'w')

Last_MD5='xXxXxX'

for i in range(1, len(FileDB) - 1):

    if FileDB[i][5] == 'Y':
        if Last_MD5 != FileDB[i][4] and len(FileDB[i][4]) > 0:
            OutFile.write('\n')

        OutFile.write('\n#    (' + FileDB[i][4] + ') ' + FileDB[i][1] + ' Size:' + str(FileDB[i][3]))
        OutFile.write('\nrm "' + FileDB[i][1]+'"')

        DuplicatesCount+=1

        # print('#    ' + FileDB[i][4] + ' MD5:' + FileDB[i][1] + ' Size:' + str(FileDB[i][3]))
        # print('rm "' + FileDB[i][1]+'"')

        Last_MD5 = FileDB[i][4]

    elif FileDB[i][5] == 'X':
        if Last_MD5 != FileDB[i][4] and len(FileDB[i][4]) > 0:
            OutFile.write('\n')

        OutFile.write('\n#    (' + FileDB[i][4] + ') ' + FileDB[i][1] + ' Size:' + str(FileDB[i][3]))
        OutFile.write('\n# PRESERVE "' + FileDB[i][1] + '"')
        # print('#    ' + FileDB[i][4] + ' MD5:' + FileDB[i][1] + ' Size:' + str(FileDB[i][3]))
        # print('# preserved dir ' + FileDB[i][1])

        Last_MD5 = FileDB[i][4]

    elif FileDB[i][5] == 'K':
        if Last_MD5 != FileDB[i][4] and len(FileDB[i][4]) > 0:
            OutFile.write('\n')

        OutFile.write('\n#    (' + FileDB[i][4] + ') ' + FileDB[i][1] + ' SAVE Size:' + str(FileDB[i][3]))
        OutFile.write('\n# KEEP "' + FileDB[i][1]+ '"')
        # print('#    ' + FileDB[i][4] + ' MD5:' + FileDB[i][1] + ' Size:' + str(FileDB[i][3]))
        # print('# Keep file ' + FileDB[i][1])

        Last_MD5 = FileDB[i][4]

OutFile.close()


if len(DatabaseFile)>0:

    #   Save the database
    # root = ET.Element("FDF_Files")
    root = etree.Element("root")

    for i in range(1, len(FileDB) - 1):

        if FileDB[i][3] > 250:

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


            #ET.SubElement(doc, "filename").text = FileDB[i][0]
            #ET.SubElement(doc, "fullfilename").text = FileDB[i][1]
            #ET.SubElement(doc, "modtime").text = FileDB[i][2]
            #ET.SubElement(doc, "size").text = str(FileDB[i][3])
            #ET.SubElement(doc, "MD5").text = FileDB[i][4]

    tree = etree.ElementTree(root)
    tree.write(DatabaseFile,pretty_print=True)

    #OutFile = open(DatabaseFile, 'w')
    #OutFile.write(str(etree.tostring(root, pretty_print=True)))
    #OutFile.close()


print("Finished")
print("Stats:")
print("  Total files scanned:"+str(len(FileDB)))
print("  Potential duplicates (filesizes the same):"+str(MD5CalculatedCount+MD5KeptCount))
print("  Calculated SHA256 for files:"+str(MD5CalculatedCount))
print("  Count of SHA256 calculations saved due to database:"+str(MD5KeptCount))
print("")
print("  Total duplicates found:"+str(DuplicatesCount))
