#!/usr/bin/python
#********************************HGTOOLS********************************
import time
import subprocess
import logging

#	Function takes str_sql, connects to the database, and returns 
#	the passed query results.
def hgt_query(str_sql, qtype=''):

	hgt_logger = logging.getLogger('hgt_logger')

	start = time.clock()
	user='wnrmndn_remote'
	password='^kb?i8kLByDL!'
	database='wnrmndn_hgtools'
	host='hgtools.normandindev.net'
	
	cmd=['mysql', '-h', host, '-u', user, '-p{}'.format(password), '-D', 
		database, '-Bse', str_sql]
		
	retval = subprocess.check_output(cmd)
	hgt_logger.debug('\t Database query took %s seconds' % (time.clock()-start))
	
	return retval
	
#	Function splits returned query output into a two-dimensional list
#	and passes it to the Gtk.window for user selection
def hgtools_buildlist(dinput, store):
	
	hgt_logger = logging.getLogger('hgt_logger')
	hgt_logger.debug('\t Populating Gtk.ListStore...')
	
	hgt_loadstore(dinput, store)	
	doutput=hgtools_getchoice(store)
	
	return doutput

#	Function imports the specified infile, then writes the records
#	to the hgtools database if possible
def hgt_imports(infile):
	
	hgt_logger = logging.getLogger('hgt_logger')
	hgt_logger.info('[*] Beginning import routine')

	row_count=0

	hgt_logger.info('\t Importing file : {}'.format(infile))
			
	with open(infile, 'rb') as csvfile:
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
			hgt_logger.debug('\t Removed row in import : %s' % rows[int(j)])
			hgt_logger.debug('\t Import : %s - Input row %s' % (rows[int(j)], j))
			rows.remove(rows[int(j)])
					
		# Execute the append queries			
		for row in rows:
			hgt_logger.debug(str(row))
				
			hgt_query(hgt_qbuild('import', row), 'import')
			
			row_count += 1
	
	hgt_logger.info('\t Closing File...')
	csvfile.close()	

def validate_import(rows, csvfile):
	
	hgt_logger = logging.getLogger('hgt_logger')
	hgt_logger.info('\t Validating import format...')
	
	for row in rows:
		if (len(row)!=3 or row[0]==''):
			hgt_logger.error('\t **Check your file format : http://hgtools.normandindev.net/imports.php')
			csvfile.close()
			rows = []

#	Checks the list of records to be added and returns a list of
#	deduplicated values (chosen by the user)
def hgt_dedupe(rows):
	
	hgt_logger = logging.getLogger('hgt_logger')
	str_sql='SELECT DISTINCT hgt_text FROM hgtools ORDER BY hgt_idx ASC;'
	db_rec=trim_invalid(hgt_query(str_sql, 'dedupe'))
	rows = trim_invalid(rows[1])
	
	hgt_logger.info('[*] Running De-Duplication')
	hgt_logger.debug('\t Database records : {}'.format(len(db_rec)))
	hgt_logger.debug('\t Import records : {}'.format(len(rows)))
	hgt_logger.debug('\t Comparisons : {}'.format(len(db_rec)*len(rows)))
	
	dedupe_list, stats = dd_match(rows, db_rec, 0.0)
	
	hgt_logger.info('\t Dedupe Run Complete')
	hgt_logger.debug('\t Dedupe took {} seconds'.format(stats[2]))
	hgt_logger.debug('\t Dedupe List Length : {}'.format(len(dedupe_list)))
	hgt_logger.debug('\t Successful Comparisons : {}'.format(stats[0]))
	hgt_logger.debug('\t Potential Duplicates : {}'.format(stats[1]))
		
	store = Gtk.ListStore('gboolean', int, str, int, str, str, str)
	hgt_loadstore(dedupe_list, store)
	dups=hgtools_dd_choose(store, stats)
	
	hgt_logger.debug('\t Identified duplicates : {}'.format(len(dups)))
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
