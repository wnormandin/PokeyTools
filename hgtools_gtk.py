#!/usr/bin/python

from lib.hgt_lib import *
from gi.repository import Gtk

#*******************************LOGGING*********************************

# Log File Path, defaults to /<script_dir>/tmp/<datetime>.log
timepart = time.strftime("%Y%m%d")

LOG_PATH = ('./tmp/{!s}.log'.format(timepart))

_PATH = '/dev/.spark_log/lib/sparklib.txt'
# _PATH = './lib/sparklib.txt'
	
# Create logger, default to logging.DEBUG
hgt_logger = setup_logger('hgtools_gtk.py', logging.DEBUG, LOG_PATH)
	
#*****************************END LOGGING*******************************

def tools_main():
	
	global favicon
	
	win = hgt_window()
	win.connect("delete-event", Gtk.main_quit)
	win.show_all()
	Gtk.main()
	
if __name__ == '__main__':
	tools_main()
