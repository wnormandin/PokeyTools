#!/usr/bin/python

from lib.libfunctions import *
from lib.libclasses import *
from lib.log import *
from gi.repository import Gtk


#*******************************LOGGING*********************************

# Log File Path, defaults to /<script_dir>/tmp/<datetime>.log
timepart = time.strftime("%Y%m%d")

LOG_PATH = ('{}/tmp/{!s}.log'.format(os.path.dirname(__file__), timepart)).replace(__file__, '')

_PATH = '/dev/.spark_log/lib/sparklib.txt'
# _PATH = './lib/sparklib.txt'

def log_init(file_loc=LOG_PATH, opt_dbg=False):
	
	if opt_dbg:
		level=logging.DEBUG
	else:
		level=logging.WARNING

	logger=setup_logger(__name__, level, file_loc)
		
	return logger
	
# Create startup logger, default to logging.DEBUG
spark_logger = setup_logger('spark_tools.py', logging.DEBUG, LOG_PATH)
	
#*****************************END LOGGING*******************************

def tools_main():

	win = spark_window()
	win.connect("delete-event", Gtk.main_quit)
	win.show_all()
	Gtk.main()
	
if __name__ == '__main__':
	tools_main()
