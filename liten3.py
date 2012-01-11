#!/usr/bin/env python
#Liten2 - Deduplication command line tool
#Author: Alfredo Deza (Initial Development by Noah Gift)
#License: GPLv3 License
#Email: alfredodeza [at] gmail dot com

__version__ = "0.0.2"
__date__ = "2009-03-06"

"""
Liten2 walks through a given path and creates a Checksum based on
the Sha1 library storing all the data in a Sqlite3 database.
You can run different kinds of reports once this has been done,
which gives you the ability to determine what files to delete.
"""
import os
import optparse
import sys
import hashlib
import sqlite3
import time



#MUST CLEAR
from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
                        FileTransferSpeed, FormatLabel, Percentage, \
                        ProgressBar, ReverseBar, RotatingMarker, \
                        SimpleProgress, Timer



db_name = time.strftime('%Y_%m_%d@%H_%M_%S.sqlite3')


class Walk(object):
    """Takes charge of harvesting file data"""
    
    def __init__(self, path, size=1048756):
        self.path = path
        self.size = size



    def findthis(self):
        """Walks through and entire directory to create the checksums exporting
        the result at the end."""
        db = DbWork()
	
        searched_files = 0
	print self.path
	number_of_files = sum(len(filenames) for path, dirnames, filenames in os.walk(self.path))
	
	print "Number of files to scan : %s" %number_of_files
        pbar = ProgressBar(widgets=[Percentage(), Bar()], maxval=number_of_files).start()
        for root, dir, files in os.walk(self.path):
    	  #for i in range(number_of_files):
	
            for f in files:
                searched_files += 1
		
                try:
                    absolute = os.path.join(root, f)
                    if os.path.isfile(absolute):
                        size = os.path.getsize(absolute)
			
			pbar.update((searched_files-1)+1)
                        if size > self.size:
			
                            readfile = open(absolute).read(16384)
                            sh = hashlib.sha224(readfile).hexdigest()
                            db.insert(absolute, size, sh)
            
                except IOError:
                    pass
	pbar.finish()
        db.insert_opts(searched_files, self.size)
        db.export()
	


class Report(object):
    """Builds a full or specific report"""
    
    def __init__(self,dump=db_name,full=True):
        self.dump = dump
        self.full = full
        if os.path.isfile(self.dump):
            self.sqlfile = open(self.dump, 'r')
            self.conn = sqlite3.connect(':memory:', isolation_level='exclusive')
            self.c = self.conn.cursor()
            for i in self.sqlfile.readlines():
                self.c.executescript(i)
        else:
            print "SQL file not found. Run liten2.py to build a new one."
            sys.exit(1)
            
        if self.full:
            self.fullreport()
    
    def fullreport(self):
        """Returns all reports available"""
        for dup_count in self.count_dups():
            print ""
            print "Duplicate files list"
        print "--------------------------------------"
        for paths in self.path_dups():
            print "%smb ::  %s" %(self.humanvalue(paths[2]) , paths[0])
            
        print ""
        print "Liten2 Full Reporting"
        print "--------------------------------------"
        for dup_count in self.count_dups():
            print "Duplicate files found:\t %s" % dup_count[0]
        for getsize in self.size_searched():
            print "File Size searched:\t %s MB" % self.humanvalue(getsize[0])        
        print "Total MB wasted:\t %s MB" % self.totalmb()
        for i in self.file_num():
            print "Files found over %s MB:\t %s" % (self.humanvalue(getsize[0]), i[0])
        for i in self.total_files():
            print "Total files searched:\t %s" % i[0]
        print ""
        print "To delete files, run liten2 in interactive mode:\npython liten2.py -i"
        
    def total_files(self):
        """Return Absolute total of files searched"""
        command = "SELECT searched FROM options;"
        return self.c.execute(command)
        
    def size_searched(self):
        """Return the Size searched"""
        command = "SELECT size FROM options;"
        return self.c.execute(command)
        

    def count_dups(self):
        """Counts the number of duplicate files"""
        command = "SELECT COUNT(path) FROM files WHERE checksum IN (SELECT\
                  checksum FROM files GROUP BY checksum HAVING\
                  COUNT(checksum) >1) ORDER BY checksum;"
        return self.c.execute(command)
    
    def path_dups(self):
        """Gets all the duplicate files along with the absolute paths"""
        command = "SELECT path, checksum, bytes FROM files WHERE checksum IN (SELECT\
                  checksum FROM files GROUP BY checksum HAVING\
                  COUNT(checksum) >1) ORDER BY bytes;"
        return self.c.execute(command)

    def size_dups(self):
        """Gets the size of duplicate entries"""
        command = "SELECT bytes FROM files WHERE checksum in (SELECT\
                  checksum FROM files GROUP BY checksum HAVING\
                  COUNT(checksum) >1) ORDER BY checksum;"
        return self.c.execute(command)
        
    def file_num(self):
        """Return the total number of files over searched size found"""
        command = "SELECT COUNT(id) FROM files;"
        return self.c.execute(command)
        
    def totalmb(self):
        """Total size in Megabytes of space used by duplicate files"""
        megabytes = 0
        for i in self.size_dups():
            megabytes += i[0]
        if megabytes:
            return self.humanvalue(megabytes)
        else:
            return 0
    
        
    def humanvalue(self, value):
        """returns a human value for a file in MegaBytes"""
        if value > 1024 * 1024 * 1024:
            return "%d" % (value / 1024 / 1024 / 1024 / 1024)
        if value > 1024 * 1024:
            return "%d" % (value / 1024 / 1024)
        if value > 1024:
            return "%d" % (value / 1024 / 1024)


class DbWork(object):
    """All the Database work happens here"""
    
    def __init__(self):
        self.conn = sqlite3.connect(':memory:', isolation_level = 'exclusive')
        self.c = self.conn.cursor()
        self.createtable1 = 'CREATE TABLE files (id integer primary key,\
                           path TEXT, bytes INTEGER,checksum TEXT)'
        self.createtable2 = 'CREATE TABLE options (id integer primary key,\
                            searched INTEGER, size INTEGER)'
        self.c.execute(self.createtable1)
        self.c.execute(self.createtable2)
        self.conn.commit()
        self.conn.text_factory = str
        self.database = db_name
        

    def insert(self, fileinfo, size, checksum):
        """Inserts the file information into the database"""
        values = (fileinfo, size, checksum)
        command = "INSERT INTO files (path, bytes, checksum) \
                  VALUES(?, ?, ?)"
        self.c.execute(command, values)
        self.conn.commit()
        
    def insert_opts(self, searched_files, size):
        """Insert optional information"""
        values = (searched_files, size)
        command = "INSERT INTO options (searched, size) VALUES(?, ?)"
        self.c.execute(command, values)
        self.conn.commit()

    def export(self):
        """ Exports the whole memory database to a sql file"""
        f = open(self.database, 'a')
        for line in self.conn.iterdump():
            f.write(line)
        self.c.close()

class Interactive(object):
    """This mode creates a session to delete files"""
    
    def __init__(self,
                 dryrun=False):
        self.dryrun = dryrun
        self.dump = strftime('%Y-%m-%d.sql')
        if os.path.isfile(self.dump):
            self.sqlfile = open(self.dump, 'r')
            self.conn = sqlite3.connect(':memory:', isolation_level='exclusive')
            self.c = self.conn.cursor()
            for i in self.sqlfile.readlines():
                self.c.executescript(i)
        else:
            print "SQL file not found for interactive mode. Run liten2.py to build a new one."
            sys.exit(1)
            
    def session(self):
        "starts a new session"
        single = []
        for_deletion = []
        dups = Report(full=False)
        for duplicates in dups.path_dups():
            if duplicates[1] not in single:
                single.append(duplicates[1])

        if self.dryrun:
            print "\n#####################################################"
            print "# Running in DRY RUN mode. No files will be deleted #"
            print "#####################################################\n"
        print """
\t LITEN 2 \n

Starting a new Interactive Session.

* Duplicate files will be presented in numbered groups.
* Type one number at a time
* Hit Enter to skip to the next group.
* Ctrl-C cancels the operation, nothing will be deleted.
* Confirm your selections at the end.\n
-------------------------------------------------------\n"""

        try:
            for checksum in single:
                group = self.separate(checksum)
                count = 1
                match = {}
                for i in group:
                    match[count] = i[0]
                    print "%d \t %s" % (count, i[0])
                    count += 1
                numbers = []
                try:
                    answer = True
                    while answer:
                        choose = int(raw_input("Choose a number to delete (Enter to skip): "))
                        if match.get(choose) not in for_deletion:
                            for_deletion.append(match.get(choose))
                        if not choose:
                            answer = False
                            
                except ValueError:
                    print "--------------------------------------------------\n"
            
            print "Files selected for complete removal:\n"
            for selection in for_deletion:
                if selection:
                    print selection
            print ""
            if self.dryrun:
                print "###########################"
                print "# DRY RUN mode ends here. #"
                print "###########################\n"
            if not self.dryrun:
                confirm = raw_input("Type Yes to confirm (No to cancel): ")
                if confirm in ["Yes", "yes", "Y", "y"]:
                    for selection in for_deletion:
                        if selection:
                            
                            try:
                                print "Removing file:\t %s" % selection
                                os.remove(selection)
                            except OSError:
                                "Could not delete:\t %s \nCheck Permissions" % selection
            else:
                print "Cancelling operation, no files were deleted."
                    
        except KeyboardInterrupt:
            print "\nExiting nicely from interactive mode. No files deleted\n"
                
    def separate(self, checksum):
        list = []
        dups = Report(full=False)
        for i in dups.path_dups():
            if i[1] == checksum:
                list.append(i)
        if list:
            return list

def main():
    """Parse the options"""
    p = optparse.OptionParser()
    p.add_option('--report', '-r', action="store_true",
                 help="Generates a report from a previous run")
    p.add_option('--path', '-p', help="Supply a path to search")
    p.add_option('--size', '-s', help="Search by Size in MB. Defaults to 1")
    p.add_option('--interactive', '-i', action="store_true",
                 help='Interactive mode to delete files')
    p.add_option('--dryrun', '-d', action="store_true",
                 help="Does not delete anything. Use ONLY with interactive mode")
    p.add_option('--open', '-o', help="Choose a SQL dump from another run")
    
    options, arguments = p.parse_args()
        
    if options.report:
        if options.open:
            file = options.open
            if os.path.isfile(file):
                out = Report(file)
            else:
                sys.stderr.write("\nYou have selected a non existent or invalid file\n")
                sys.exit(1)
                
        else:
            out = Report()
        return out
        
    if options.path:
        if not os.path.isdir(options.path):
            sys.stderr.write("Search path does not exist or is not a directory:\
            %s\n" % options.path)
            sys.exit(1)
        try:
            run = Walk(options.path)
            if options.size:
                mb = int(options.size)*1048576
                run = Walk(options.path, size=mb)
            run.findthis()
            out = Report()
            return out
            sys.exit(0)
            
        except (KeyboardInterrupt, SystemExit):
            print "\nExiting nicely from Liten2..."
            sys.exit(1)            
        
    if options.interactive:
        if options.dryrun:
            run = Interactive(dryrun=True)
        else:
            run = Interactive()
        run.session()

    else:
        sys.stderr.write("For help please run: \nliten2.py --help"'\n')
        sys.exit(1)

if __name__=="__main__":
    main()
