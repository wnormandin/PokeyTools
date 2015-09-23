#!/usr/bin/env python

import log
from libclasses import *
from dedupe import *
from time import sleep
from gi.repository import Gtk
import csv, locale, re
import subprocess, random, string, os, inspect, sys

#*******************************DEV LIST********************************
#
#	Add deduplication to CSV import routine
#	
#
#*****************************END DEV LIST******************************

USER_SELECTION=0

#*******************************LOGGING*********************************

hgt_logger=logging.getLogger('hgtools.py')

# Logging / Message verbosity switches
DEBUG = True
VERBOSE = True
	
#*****************************END LOGGING*******************************

#*******************************hgt_query*******************************
#
#	Function takes str_sql, connects to the database, and returns 
#	the passed query results.

def hgt_query(str_sql, qtype):
	
	start = time.clock()
	user='wnrmndn_remote'
	password='^kb?i8kLByDL!'
	database='wnrmndn_hgtools'
	host='hgtools.normandindev.net'
	
	cmd=['mysql', '-h', host, '-u', user, '-p%s'%password, '-D', 
		database, '-Bse', str_sql]
		
	hgt_logger.debug('hgt_query command : ' + str(cmd))
		
	proc=subprocess.Popen(cmd,stdout=subprocess.PIPE)
	retval=hgt_parse(proc.communicate()[0], qtype)
	
	hgt_logger.debug('hgt_query return : ' + str(retval).replace('\n', ' '))
	hgt_logger.debug('hgt_query took %s seconds' % (time.clock()-start))
	
	return retval
	
#*****************************END hgt_query*****************************

#*******************************hgt_imports*****************************
#
#	Function imports the specified infile, then writes the records
#	to the hgtools database if possible

def hgt_imports(infile):

	row_count=0

	hgt_logger.info('Importing file : %s' % infile)
			
	with open(infile, 'rb') as csvfile:
		
		hgt_logger.info('File found, reading...')
		file_read = csv.reader(csvfile, delimiter=',', quotechar="'")
		
		rows = []
		for row in file_read:
			
			hgt_logger.debug(row)
			rows.append(row)
		
		validate_import(file_read, csvfile)
		
		dups = hgt_dedupe(rows).sort(reverse=True)
		
		# Delete the duplicates from the list to be uploaded
		hgt_logger.debug('Input Array Row Count : %s' % len(rows))
		for j in set(dups):
			hgt_logger.debug('Removed row in import : %s' % rows[int(j)])
			hgt_logger.debug('Import : %s - Input row %s' % (rows[int(j)], j))
			rows.remove(rows[int(j)])
					
		# Execute the append queries			
		for row in rows:
			hgt_logger.debug(str(row))
				
			hgt_query(hgt_qbuild('import', row), 'import')
			
			row_count += 1
	
	hgt_logger.info('Closing File...')		
	csvfile.close()	

def validate_import(rows, csvfile):
	
	hgt_logger.info('Validating import format...')
	
	for row in rows:
		if (len(row)!=3 or row[0]==''):
			hgt_logger.info('Check your file format : http://hgtools.normandindev.net/imports.php')
			csvfile.close()
			sys.exit(3)
	
#******************************hgt_dedupe*******************************
#
#	Checks the list of records to be added and returns a list of
#	deduplicated values (chosen by the user)

def hgt_dedupe(rows):
	
	str_sql='SELECT DISTINCT hgt_text FROM hgtools ORDER BY hgt_idx ASC;'
	db_rec=trim_invalid(hgt_query(str_sql, 'dedupe'))
	rows = trim_invalid(rows[1])
	
	hgt_logger.info('Running De-Duplication')
	hgt_logger.debug('Database records : ' + str(len(db_rec)))
	hgt_logger.debug('  -- Import records : ' + str(len(rows)))
	hgt_logger.debug('  -- Comparisons : ' + str(len(db_rec)*len(rows)))
	
	dedupe_list, stats = dd_match(rows, db_rec, 0.0)
	
	hgt_logger.info('Dedupe Run Complete')
	hgt_logger.debug('Dedupe took %s seconds' % str(stats[2]))
	hgt_logger.debug('Dedupe List Length : %s' % str(len(dedupe_list)))
	hgt_logger.debug('Successful Comparisons : %s' % str(stats[0]))
	hgt_logger.debug('Potential Duplicates : %s' % str(stats[1]))
		
	store = Gtk.ListStore('gboolean', int, str, int, str, str, str)
	hgt_loadstore(dedupe_list, store)
	dups=hgtools_dd_choose(store, stats)
	
	hgt_logger.debug('Identified duplicates : %s' % str(dups))
	
	return dups
	
def trim_invalid(rows):
	out_rows = []
	for row in rows:
		if len(row)>1:
			out_rows.append(row)
	return out_rows
	
def hgt_dedupe_test():
	
	hgt_logger.info('Dedupe Test Started')
	
	dedupe_list, stats = dd_test()
	
	hgt_logger.info('Dedupe Run Complete')
	hgt_logger.debug('Dedupe took %s seconds' % str(stats[2]))
	hgt_logger.debug('Dedupe List Length : %s' % str(len(dedupe_list)))
	hgt_logger.debug('Successful Comparisons : %s' % str(stats[0]))
	hgt_logger.debug('Potential Duplicates : %s' % str(stats[1]))
	
	store = Gtk.ListStore('gboolean', int, str, int, str, str, str)
	
	hgt_loadstore(dedupe_list, store)
	non_dups=hgtools_dd_choose(store, stats)
	
	hgt_logger.debug('Identified duplicates : %s' % str(non_dups))
	
	return non_dups

def hgtools_dd_choose(store, stats):
	
	win = gtk_dedupe_selections(store, stats)
	win.connect("delete-event", Gtk.main_quit)
	win.set_position(Gtk.WindowPosition.CENTER)
	win.show_all()
	Gtk.main()
		
	return win.selected
			
#******************************build_query******************************
#
#	Function returns a MySQL query string str_sql based on the passed
#	argument and option

def hgt_qbuild(qtype, qcode=''):
	
	if qtype=='tool':
		str_sql='SELECT hgt_text FROM hgtools WHERE hgt_code="' + qcode + '";'
		
	if qtype=='import':
		str_sql="INSERT INTO `hgtools` (`hgt_code`, `hgt_text`, `hgt_group`) VALUES ('"
		str_sql += qcode[0] + "', '" + qcode[1] + "', '" + qcode[2] + "');"
		
	if qtype=='phrases':
		str_sql = 'SELECT hgt_code, hgt_text, hgt_desc FROM '
		str_sql += '(SELECT * FROM hgtools LEFT JOIN hgtools_codes '
		str_sql += 'ON hgtools.hgt_code=hgtools_codes.code) AS hgt_temp '
		str_sql += "WHERE hgt_code LIKE '%" + qcode + "%' OR "
		str_sql += "hgt_text LIKE '%" + qcode + "%' OR "
		str_sql += "hgt_desc LIKE '%" + qcode + "%';"
		
	# 'test' will query the most recent hgtools version information	
	elif qtype=='test':
		str_sql = 'SELECT about_release, about_timestamp, about_desc '
		str_sql += 'FROM hgtools_about '
		str_sql += 'WHERE about_idx='
		str_sql += '(SELECT MAX(about_idx) FROM hgtools_about);'
	
	hgt_logger.debug('build_query SQL : %s' % str_sql)
	return str_sql
	
#****************************END build_query****************************

#*****************************hgt_parse*****************************
#
#	Function takes potential multiline text output and determines the 
#	number of lines, if >1 a random line is returned from the results
#	or returns a list of arguments for the user to select from in a
#	dialogue box.

def hgt_parse(outp, qtype):
	
	outlist = outp.splitlines()
	
	hgt_logger.debug('Return list length : %s' % str(len(outlist)))
	hgt_logger.debug('hgt_parse opt : %s' % qtype)
	hgt_logger.debug('hgt_parse outp : %s' % outp.replace('\n', ' '))
	
	if len(outlist)==1 and qtype=='test':
		test_out=outlist[0].split("\t")
		hgt_logger.info('Version : %s' % test_out[0])
		hgt_logger.info('Description : %s' % test_out[2])
		hgt_logger.info('Release Date : %s' % test_out[1])
		retval="Success!"
		hgt_paths()
		
	elif len(outlist)>1 and qtype=='phrases':
		store = Gtk.ListStore(str, str, str)
		qchoice=hgtools_buildlist(outlist, store)
		retval=hgt_query(hgt_qbuild('tool', qchoice), 'tool')
						
	elif len(outlist)>1 and qtype=='dedupe':
		retval=outlist
		
	elif len(outlist)==1:
		retval=outlist[0]
		
	elif len(outlist)>1 and qtype=='tool':
		retval=outlist[random.randint(0, len(outlist)-1)]
		
	else:
		hgt_logger.warning('Query returned zero rows')
		retval = None
	
	return retval
	
#*****************************END hgt_parse*****************************

#***************************hgtools_buildlist***************************
#
#	Function splits returned query output into a two-dimensional list
#	and passes it to the Gtk.window for user selection

def hgtools_buildlist(dinput, store):
	
	hgt_logger.debug('Populating Gtk.ListStore...')
	
	hgt_loadstore(dinput, store)	
	doutput=hgtools_getchoice(store)
		
	return doutput
	
def hgt_loadstore(dinput, store):
	
	for i in range(0, len(dinput)):
		try:
			store.append(dinput[i].split("\t"))
		except AttributeError:		
			store.append(list(dinput[i]))
		except ValueError:
			store.append(str(list(dinput[i])))

#**************************END hgtools_buildlist************************

#***************************hgtools_getchoice***************************
#
#	Function provides the user with a list, returns selected value

def hgtools_getchoice(store):
	
	win = gtk_show_window(store)
	win.connect("delete-event", Gtk.main_quit)
	win.set_position(Gtk.WindowPosition.CENTER)
	win.show_all()
	Gtk.main()
	
	hgt_logger.debug('gtk_show_window return : %s' % win.selected)
	return win.selected

#**************************END hgtools_getchoice************************

#*******************************hgt_paths*******************************

def hgt_paths():

	subf = ['/', '/lib/includes', '/lib/documents']
	
	hgt_logger.debug('Checking system path...')
	sleep(1)
	
	for x in subf:
		
		cmd_subfolder = os.path.realpath(os.path.abspath(
			os.path.join(os.path.split(inspect.getfile(
				inspect.currentframe()))[0],x)))

	if cmd_subfolder not in sys.path:
		hgt_logger.debug('adding %s to sys,path' % cmd_subfolder)
		sys.path.append(cmd_subfolder)
		
#*****************************END hgt_paths*****************************
