#!/usr/bin/python
#********************************HGTOOLS********************************
import time
import subprocess
import logging

#	Function takes str_sql, connects to the database, and returns 
#	the passed query results.
def hgt_query(str_sql, qtype=''):

	pokeylogger = logging.getLogger('pokeylogger')

	start = time.clock()
	user='wnrmndn_remote'
	password=''
	database='wnrmndn_hgtools'
	host='hgtools.normandindev.net'
	
	cmd=['mysql', '-h', host, '-u', user, '-p{}'.format(password), '-D', 
		database, '-Bse', str_sql]
		
	retval = subprocess.check_output(cmd)
	pokeylogger.debug('\t Database query took %s seconds' % (time.clock()-start))
	
	return retval
	
#	Function splits returned query output into a two-dimensional list
#	and passes it to the Gtk.window for user selection
def hgtools_buildlist(dinput, store):
	
	pokeylogger = logging.getLogger('pokeylogger')
	pokeylogger.debug('\t Populating Gtk.ListStore...')
	
	hgt_loadstore(dinput, store)	
	doutput=hgtools_getchoice(store)
	
	return doutput

#	Function imports the specified infile, then writes the records
#	to the hgtools database if possible
def hgt_imports(infile):
	
	pokeylogger = logging.getLogger('pokeylogger')
	pokeylogger.info('[*] Beginning import routine')

	row_count=0

	pokeylogger.info('\t Importing file : {}'.format(infile))
			
	with open(infile, 'rb') as csvfile:
		file_read = csv.reader(csvfile, delimiter=',', quotechar="'")
		
		rows = []
		for row in file_read:
			
			pokeylogger.debug(row)
			rows.append(row)
		
		validate_import(file_read, csvfile)
		
		dups = hgt_dedupe(rows).sort(reverse=True)
		
		# Delete the duplicates from the list to be uploaded
		pokeylogger.debug('Input Array Row Count : %s' % len(rows))
		for j in set(dups):
			pokeylogger.debug('\t Removed row in import : %s' % rows[int(j)])
			pokeylogger.debug('\t Import : %s - Input row %s' % (rows[int(j)], j))
			rows.remove(rows[int(j)])
					
		# Execute the append queries			
		for row in rows:
			pokeylogger.debug(str(row))
				
			hgt_query(hgt_qbuild('import', row), 'import')
			
			row_count += 1
	
	pokeylogger.info('\t Closing File...')
	csvfile.close()	

def validate_import(rows, csvfile):
	
	pokeylogger = logging.getLogger('pokeylogger')
	pokeylogger.info('\t Validating import format...')
	
	for row in rows:
		if (len(row)!=3 or row[0]==''):
			pokeylogger.error('\t **Check your file format : http://hgtools.normandindev.net/imports.php')
			csvfile.close()
			rows = []

#	Checks the list of records to be added and returns a list of
#	deduplicated values (chosen by the user)
def hgt_dedupe(rows):
	
	pokeylogger = logging.getLogger('pokeylogger')
	str_sql='SELECT DISTINCT hgt_text FROM hgtools ORDER BY hgt_idx ASC;'
	db_rec=trim_invalid(hgt_query(str_sql, 'dedupe'))
	rows = trim_invalid(rows[1])
	
	pokeylogger.info('[*] Running De-Duplication')
	pokeylogger.debug('\t Database records : {}'.format(len(db_rec)))
	pokeylogger.debug('\t Import records : {}'.format(len(rows)))
	pokeylogger.debug('\t Comparisons : {}'.format(len(db_rec)*len(rows)))
	
	dedupe_list, stats = dd_match(rows, db_rec, 0.0)
	
	pokeylogger.info('\t Dedupe Run Complete')
	pokeylogger.debug('\t Dedupe took {} seconds'.format(stats[2]))
	pokeylogger.debug('\t Dedupe List Length : {}'.format(len(dedupe_list)))
	pokeylogger.debug('\t Successful Comparisons : {}'.format(stats[0]))
	pokeylogger.debug('\t Potential Duplicates : {}'.format(stats[1]))
		
	store = Gtk.ListStore('gboolean', int, str, int, str, str, str)
	hgt_loadstore(dedupe_list, store)
	dups=hgtools_dd_choose(store, stats)
	
	pokeylogger.debug('\t Identified duplicates : {}'.format(len(dups)))
	return dups
	
def trim_invalid(rows):
	out_rows = []
	for row in rows:
		if len(row)>1:
			out_rows.append(row)
	return out_rows

def hgt_loadstore(dinput, store):
	
	for i in range(0, len(dinput)):
		try:
			store.append(dinput[i].split("\t"))
		except AttributeError:		
			store.append(list(dinput[i]))
		except ValueError:
			store.append(str(list(dinput[i])))

#********************************/HGTOOLS*******************************
