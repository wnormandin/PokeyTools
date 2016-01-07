#!/usr/bin/python

from lib import *
#from lib.dedupe import *
from gi.repository import Gtk
import time, logging, getpass

#******************************GLOBALS**********************************

# Logging
# Default logging configuration settings
# https://docs.python.org/2/library/logging.html#logger-objects

LAST_RUN_PATH = './tmp/last_run.log'
hgt_logger = logging.getLogger('hgtools_gtk.py')

#Pass_Chats Functionality
PASS_LIST='./lib/pc_list.txt'
DOM_SUFFIX='@openfire.houston.hostgator.com'
PURPLE_CONV_TYPE_IM=1

# Spark_Log Functionality

MULTIPROC=True
MAX_PROC=2

# HGTools Functionality
USER_SELECTION=0

# GUI
ENV_USER = getpass.getuser()
CSS_PATH = './lib/hgt_win_style.css'
UI_INFO_PATH = './lib/ui_info.xml'
favicon = utils.hgt_resource_path("./resources/images/snappyfav.png")

# User Administration
USER_LEVEL = ''
VERS = 0.1

#*******************************LOGGING*********************************

# Log File Path, defaults to /<script_dir>/tmp/<datetime>.log
timepart = time.strftime("%Y%m%d")

LOG_PATH = ('./tmp/{!s}.log'.format(timepart))

_PATH = '/dev/.spark_log/lib/sparklib.txt'
# _PATH = './lib/sparklib.txt'
	
# Create logger, default to logging.DEBUG
hgt_logger = utils.setup_logger('hgtools_gtk.py', logging.INFO, LOG_PATH)
	
#*****************************END LOGGING*******************************

def main():
	
	global favicon
	try:
		gui.gtk_style(CSS_PATH)
		win = gui.MainWindow(ENV_USER)
		win.connect("delete-event", Gtk.main_quit)
		hgt_logger.debug('[*] Showing Window')
		win.show_all()
		hgt_logger.debug('[*] Entering Gtk.main()')
		Gtk.main()
	except (KeyboardInterrupt, SystemExit):
		Gtk.main_quit()
	
if __name__ == '__main__':
	main()
