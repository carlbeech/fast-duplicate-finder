# fast-duplicate-finder

A python program to locate duplicate files - and do it fast

HISTORY
=======

### V0.1

- Initial release

### V0.1a

- Added '-w' option to output suitable for windows command prompt
- Also, added ZIP version, contains a self-contained version with windows EXE (built using pyinstaller)
- The database file now only contains entries that have a SHA256 value, rather than all files > 250 bytes
  this cuts the database file size quite a bit.
     
### V0.2 - Major update

- Core logic now faster
- Automatically detects if linux or windows
- running `fdf_scanner.py` is the command line version
- running `fdf_scanner_gui.py` is the GUI version, using QT5.
- Windows versions are `fdf_scanner.exe` (command line) and `fdf_scanner_gui.exe` (GUI version)
       
### V0.3 - Bugfix update

- Directory separators reflect the OS
- Addition of exception handler catches crash within BinaryChopSearch function.

### V0.4

- GUI: load and save config files
- You can now save the current configuration in the GUI to a `.ini` config file
- You can now load the config from an `.ini` file to the GUI

### V0.5

- Bugfix (Many thanks for the fix from Oliver Kopp)
- Add exception code to deal with invalid timestamps for files under windows

### V0.6
- add '-g' switch to force to GUI mode as alternative to renaming the file (renaming still works)
- added low memory footprint hash calculate (files > 250Mb)
- Duplicates are located as the directories are scanned, and output files and database file
  is written for every 20 files examined.
  (file writes are fast and so there's not a major issue with time, in comparison to the benefit
  of being able to have output in case the program crashes part way through processing).

### V0.7
- Improvements - progress bar now works again properly
- progressbar now includes name of the file currently having hash calculation and its size
- works in both GUI and console modes
- output file is (re)generated for every 100 files having a hash calculation.
- progressbar takes console size into account

### V0.8
- Bug fix - crash deriving file names within linux environments

A bit of history...
===================

If you're anything like me, you'll have hundreds of photos, spread over different directories, but you don't know if you've got a file repeated a number of times (e.g. you've copied the contents of an SD card to your hard drive for 'safe keeping').

In my case, this totalled around 300Gb+ of photos and videos etc. I'd tried other duplicate finding programs, and while these worked, they were
a) horrendously slow (e.g. fslint took three days)
b) weren't that helpful in the output that they gave (e.g. fslint just gave a list of duplicate file names - not even the directory where they were.

I'd created a duplicate file finding program in GAMBAS a while ago, but I thought it's time to re-code this, and do this in Python 3. After some experimentation, the resulting program worked through the 300Gb in around 20 minutes.


FEATURES
========

The initial version of the program is a simple command line python program - I'm intending to put a GUI version here, as well as a compiled windows EXE in time.

Features of the commandline version:

* Its fast: in tests, it takes around 20 mins to scan about 300Gb of files (thats around 30,000 files).
* You can specify one or more directories to scan (e.g. `-i /my/directory -i /my/second/directory -i /my/third/directory`)
* You can 'preserve' one or more directories (see below) (e.g. `-p /my/directory/savefiles -p /my/second/directory/save`)
* The program can save the results of your duplicate finding run in a XML database file - and it can use the data on subsequent runs
* You can save all the input parameters into a configuration file, so you don't have to keep typing them in ;-)
* Pattern matching of files is performed by using SHA256, not MD5.
* The program outputs a runnable script that contains the necessary file delete commands, so you can review/ammend before you run.
* Output is generated while the filesystem is scanned so there is usable output even if you get a partial run.
* Can output linux (bash) output, or windows (batch file) output
* Automatically detects and adapts output for the OS
* Both GUI and command line versions of the program.

Key Concepts
============

Input-directories
-----------------
In my situation, I have a single 'main' directory holding all my pictures, then I go and dump all my new pictures into another directory - which could be on another part of the disk. So, I've made it so you can scan multiple input directories e.g.:
`-i /My/Master/PhotosDirectory -i "/My/Dump of SDCard"`

(note the quotes if you have spaces in your directory names!)

Preserve-directories
--------------------
If you have all your 'sorted' files in a master directory, and all your new files in another directory, the last thing you want is for the duplicate finder to delete files from your master directory and keep them in the new-files directory.
The 'preserve' directive says "if you find duplicates, don't delete files found in this directory or below"

e.g.
If you have:

```text
/My/Master/PhotosDirectory
    |
    >  Summer 2017
        |
        > smiles.jpg

/My/SDCardDump
    |
    > dc12345.jpg
```
    
Using the SHA256 comparison, the program knows that `smiles.jpg` and `dc12345.jpg` are the same, however, adding the command: `-p /My/Master/PhotosDirectory` instructs the program to not delete anything in the PhotosDirectory, or below - if duplicates are found, it will delete them from the 'other' directory - in this case, it'll delete `dc12345.jpg`.

So, using the `preserve` command, it means that you can dump all your pictures from your SD card into a directory, and once the program has finished, you'll only be left with 'new' files.

Note, you can have multiple `preserve` directories - just like multiple input directories.


Output file
-----------
The program is not intended to perform the deletions of duplicate files.
What I mean by this is that with the best of intentions, its not possible to create a bug-free program, and so, the program should never immediately perform file deletions. Instead, it'll create an output file which contains all the deletions - so that you, the user, can check it, and be happy with it before its run.

To help you check, the program outputs comments in the file so you can see if its correct - or alternatively ammend so that you switch which file is deleted and which is preserved.

for example - the output file will look something like:

```sh
#(7f8d294589939739ff779b1ac971a07006c54443dce941d7a1dff026839272b3) /home/carl/Downloads/lib/source-map/array-set.js SAVE Size:2718

#KEEP "/home/carl/Downloads/lib/source-map/array-set.js"

#(7f8d294589939739ff779b1ac971a07006c54443dce941d7a1dff026839272b3) /home/carl/Downloads/source-map/lib/source-map/array-set.js Size:2718

rm "/home/carl/Downloads/source-map/lib/source-map/array-set.js"
```

So, for each set of duplicates found, you see the SHA256 check (showing the files are the same), the location of the file and its name, and also its size.
You should also see `# KEEP "....` this is one of the duplicates, which the program has elected to keep, and
rm `"...` this is the other (duplicate) file(s), which the program has elected to delete.

Note: If you used the `preserve` option, you would see `# PRESERVE "...` against the file, rather than `# KEEP "...`

As the output is a text file of commands, you should have no difficulty in altering it if you decide to switch around which to keep and which to delete.

Windows Output
--------------
Using `-w` switches to windows output mode - this:

* adds the extension `.BAT` to the output file instead of `.SH`
* Uses appropriate commands within the file (`REM` and `DEL` instead of `#` and `rm`)
* Switches off case sensitivity for file names.
* `-w` is not mandatory - the program automatically detects linux or windows...

OK, you say its fast - how's that done? What trick has been employed?
=====================================================================
as mentioned above, in tests the program found duplicates in around 300Gb (approx 30,000 files), in around 20 minutes. There's a couple of 'tricks' being employed here:

Don't calculate SHA256 hashes for every file
--------------------------------------------
There's no point in calculating a hash value for a file if there's no other files exactly the same size - by definition, there can be no 'exactly the same file' if there are no other files of the same size. This alone makes a massive speed increase (compared with some other duplicate finders that calculate hashes for every file).  In the 30,000 file example, it meant hashes were created for around 1000 files.

Use an XML database
-------------------
By using the `-d <databasefile>` option, when the program finishes, it saves all the data its gathered to a file - including the important SHA256 values - these calculations are what take the time when running.
The next time the program is run, and you specify the database file, it initially re-reads the values in from the database file, and instead of re-calculating the hash for a file, it uses the saved value.

Note: It'll only used the saved SHA256 hash value if the file name is the same, the size is the same and the modification date time is the same.

Note2: There's nothing stopping you _not_ specifying the database file, and the program will then re-calculate the SHA256 value for the files fresh each time.

Oh, by the way, the 20 minutes example was _before_ the XML database save was used - when the database file was used the time came down to around 6 minutes :-)

Configuration file
==================
There's quite a number of parameters that can be entered, and if you run this on a regular basis, it can be painful to keep typing in.
By using the `-c <configfile>` option, you can have these pre-defined in INI format e.g.:

```INI
[InputDirectories]
InputDirectory=/home/carl/Dropbox
InputDirectory2=/home/carl/Documents
InputDirectory3=/home/carl/AnotherDirectory

[OutputFile]
OutputFileName=/home/carl/Dropbox/CARL/Development

[DatabaseFile]
DatabaseFileName=/home/carl/Dropbox/CARL/Development/scandb.xml

[PreserveDirectories]
PreserveDirectory=/home/carl/Dropbox/Development
PreserveDirectory2=/home/carl/Dropbox/ADirectoryToPreserve

(Note: if you put these in, then output format will be switched to windows style!)
[WindowsOutput]
WindowsOutput=1
```

These INI entries correspond to the input parameters of the program.

NOTE: If you use the `-c` option, you can still use the other `-i` and `-p` options - the extra ones on the command line are just added to the ones defined in the configuration file...

USE
===

```terminal
fdf_scanner.py -i <inputdir> [-i <inputdir>] [-p <preservedir>] [-p preservedir] [-d <databaseSavefile>] [-o <outputfile>] [-w] [-g]
```

Happy De-duplicating!

Carl.
