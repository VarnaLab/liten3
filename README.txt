#################
#    LITEN 2    #
#################

Author: Alfredo Deza
Version: 0.0.2
Date: Apr 20h 2009
Contact: alfredodeza at gmail.com
License: GPLv3 

Liten2 will search a given directory and find duplicate files building a report at the end.

Uses a SQLite DB to store searches and optimize file handling after it has run.

SHA-224 is used as a checksum method, this will provide for a better and more precise way of handling differences in files. 
We have updated the bytes Liten2 reads to create the checksum from 8 kilobytes to 16. This will make Liten2 create a better checksum.

Currently working on GNU/Linux and Mac OS Operating Systems only.

Setup
-----
This was developed with python 2.6 and has not been tested with earlier versions of Python. No installation is currently necessary, just uncompress the TAR file and run the file with Python.


Dependencies
------------
Liten2 depends on SQLite3. This will not be a problem in a normal Python install. However, it will not work with earlier versions of Python because we are using functionality found in Python2.6
Download and Uncompress

tar xzvf Liten2-*.tar.gz


First Time Run
--------------
For the first time run you need to supply a path to search with the "-p" flag:

python liten2.py -p /path/to/directory

This will output a SQL file where the reports will generated from in a Date format like: YEAR-MONTH-DAY.sql
Duplicate Report

Once Liten2 has run there is no need to run it again to re-read the reports:

python liten2.py -r

This will re-read the SQL file that was dumped in the previous run. 
NOTE: Liten2 will only look for the SQL file with today's date, as for now, you can't tell liten2 to choose from a different SQL file.


Interactive Delete Session
--------------------------
Liten2 has an interactive session (you need to have run liten2.py before) that will group identical files together and will let you choose the files to delete:

python liten2.py -i

When interactive mode, you can hit Ctrl-C to quit (nothing will be deleted). The group of identical files will be numbered and you will be asked to type a number to delete or hit Enter to skip to the next group.


Dry Run
-------
A Dry Run option is available only when running the interactive mode. Nothing will be deleted when this option is used. Identical files will be shown and your selections will be saved. At the end of the session a message will display that nothing was deleted. To use this option:

python liten2.py -i -d


Choose File Size to Search
--------------------------
By default, Liten2 will search for files over 1 megabyte in size. You can specify a larger size (always in megabytes) to search with the "-s" flag:

python liten2.py -s 5 -p /path/to/directory

The command above will search for files over 5 megabytes in size in the given directory path.
Issues

Any problems, issues or requests for features: alfredodeza at gmail dot com




