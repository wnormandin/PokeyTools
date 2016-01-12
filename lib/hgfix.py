#!/usr/bin/python
#************************hgfix functionality****************************

import urllib2
import urllib
import re
from gi.repository import Gtk, Gdk
from subprocess import Popen, PIPE

def hgfix_do_encode(post_arguments):

	# Encode It Properly
	uri = urllib.urlencode(post_arguments)
	uri = uri.encode('utf-8') # data should be bytes
	
	return urllib2.Request('http://hgfix.net/paste/api/create', uri)
	
def hgfix_do_post(request):

	# Make a POST Request
	response = urllib2.urlopen(request)
	
	# Read the Response
	paste_url = response.read().decode("utf-8").rstrip()  
	match = re.search(r"http://hgfix.net/paste/view/(.+)", paste_url)
	paste_url = "http://hgfix.net/paste/view/raw/" + match.group(1)
	
	return paste_url
	
def hgfix_do_paste(value, destination=False):
	
	if not destination:
		pass

	elif destination == 'clipboard':
		clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		clip.set_text(value, -1)
		
	elif destination == 'mouse':
		p = Popen(['xsel', '-p'], stdin=PIPE)
		p.communicate(value)
		
def hgfix_main(txt, destination):

	hgfix_do_paste("Loading -- Try again in a moment")
	# Pair Up the URI Query String
	post_arguments = {'text' : txt, 'private': '', 'expires': '30', 'lang': 'text'}
	ret_url = hgfix_do_post(hgfix_do_encode(post_arguments))
	hgfix_do_paste(ret_url, destination) 
