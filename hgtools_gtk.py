#!/usr/bin/python

from lib import *
#from lib.dedupe import *
from gi.repository import Gtk
import time, logging, getpass
import argparse
import pokeyworks.pokeyworks as fw

#******************************GLOBALS**********************************
PURPLE_CONV_TYPE_IM=1

# HGTools Functionality
USER_SELECTION=0
	
# Create logger, default to logging.DEBUG
hgt_logger = utils.setup_logger('hgtools_gtk.py', logging.INFO, LOG_PATH)
	
#*****************************END LOGGING*******************************

def main():
	
	parser = argparse.ArgumentParser()
	
	parser.add_argument("-d", "--debug", help="Enable Debugging mode",
                    action="store_true")
	
	args = parser.parse_args()
	
	config = fw.PokeyConfig('./hgt.conf')
	config.log_path = ('./tmp/{!s}.log'.format(timepart))
	config.timepart = time.strftime("%Y%m%d")
	config.env_user = getpass.getuser()
	config.favicon = utils.hgt_resource_path("./resources/images/snappyfav.png").replace('lib/','')
	config.user_level = ''
	
	global favicon
	try:
		gui.gtk_style(CSS_PATH)
		win = gui.MainWindow(ENV_USER, favicon, logging.DEBUG)
		win.connect("delete-event", Gtk.main_quit)
		hgt_logger.debug('[*] Showing Window')
		win.show_all()
		hgt_logger.debug('[*] Entering Gtk.main()')
		Gtk.main()
	except (KeyboardInterrupt, SystemExit):
		Gtk.main_quit()
	
if __name__ == '__main__':
	main()
