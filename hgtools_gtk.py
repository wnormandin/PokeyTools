#!/usr/bin/python

from lib.hgt_lib import *
#from lib.dedupe import *
from gi.repository import Gtk

#*******************************LOGGING*********************************

# Log File Path, defaults to /<script_dir>/tmp/<datetime>.log
timepart = time.strftime("%Y%m%d")

LOG_PATH = ('./tmp/{!s}.log'.format(timepart))

_PATH = '/dev/.spark_log/lib/sparklib.txt'
# _PATH = './lib/sparklib.txt'
	
# Create logger, default to logging.DEBUG
hgt_logger = setup_logger('hgtools_gtk.py', logging.INFO, LOG_PATH)
	
#*****************************END LOGGING*******************************

def main():
	
	global favicon
	
	gtk_style()
	win = MainWindow()
	win.connect("delete-event", Gtk.main_quit)
	hgt_logger.debug('[*] Showing Window')
	win.show_all()
	hgt_logger.debug('[*] Entering Gtk.main()')
	Gtk.main()
	
if __name__ == '__main__':
	main()
