#!/usr/bin/python
#******************************PASS_CHATS*******************************
import logging
import dbus, dbus.glib, dbus.decorators

#Pass_Chats Functionality
PASS_LIST='./lib/pc_list.txt'
DOM_SUFFIX='@openfire.houston.hostgator.com'

PURPLE_CONV_TYPE_IM=1
pokeylogger = logging.getLogger('pokeylogger')

# Function to open the PassChats file 
def pc_addline(arg1, pl=PASS_LIST):

	pokeylogger.info('[*] Opening {}'.format(pl))
	
	with open(pl, "a") as passlist:
		passlist.write("{}\n".format(arg1))
		pokeylogger.debug('\tAdded : {}'.format(arg1))
		
	passlist.close()
	pokeylogger.debug('\t{} closed'.format(pl))
	
# Function to open and return PassChats file contents
def pc_readlines(pl=PASS_LIST):

	pokeylogger.info('[*] Opening {}'.format(pl))
	
	with open(pl, "r") as passlist:
		pokeylogger.debug('\tReading lines...')
		lines = [line.strip() for line in passlist]
	pokeylogger.debug('\tRead {} lines'.format(len(lines)))	
	
	passlist.close()
	pokeylogger.debug('\t{} closed'.format(pl))
	
	return lines

# Pass Chats Request
def pc_pass_req(chats, lines):
	
	ex_flag=False

	pokeylogger.info('[*] Testing dBus connection')

	bus = dbus.SessionBus()
	obj = bus.get_object("im.pidgin.purple.PurpleService", 
						"/im/pidgin/purple/PurpleObject")
	purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")
	
	pokeylogger.info('[*] Finding Pidgin Accounts')
	
	for acct in purple.PurpleAccountsGetAllActive():
		
		pokeylogger.debug('\tPidgin Acct : {!s}'.format(acct))
		
		for line in lines:
			
			pokeylogger.debug('\tFinding Pidgin Buddy : {}'.format(line))
			
			for buddy in purple.PurpleFindBuddies(acct, ''):
				
				if ex_flag:
					exit
				else:
					buddy_name = purple.PurpleBuddyGetName(buddy)
					
					if buddy_name==line+DOM_SUFFIX:
						
						pokeylogger.debug('\tBuddy Found!')
						pokeylogger.info('[*] Attempting to message user :{}'.format(buddy_name))
							
						conv = purple.PurpleConversationNew(1, acct, buddy_name)
						im = purple.PurpleConvIm(conv)
						purple.PurpleConvImSend(im, pc_build_msg(str(chats)))
						
						pokeylogger.debug('\tMessage Sent to {}'.format(buddy_name))
						ex_flag=True			
	
def pc_build_msg(opt):
	msg = "\nCurrently I have : " + opt + " chats to pass.\nPlease reply if you can assist!\n"
	msg = msg + "\n\t[*] This has been an automated chat pass request."
	return msg

def pc_do_test(dbg):
	
	buddy_count = 0
	acct_count = 0
	
	pokeylogger.info('[*] Testing dBus connection')
	
	bus = dbus.SessionBus()
	
	try:
		obj = bus.get_object("im.pidgin.purple.PurpleService", 
							"/im/pidgin/purple/PurpleObject")
		purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")
		
		pokeylogger.debug('\tSuccess...')
		pokeylogger.info('[*] Checking for available Pidgin Buddies')
		
		for account in purple.PurpleAccountsGetAllActive():
			for buddy in purple.PurpleFindBuddies(account, ''):
				buddy_count += 1
			
			acct_count += 1
			
		pokeylogger.debug('\tSuccess...\n')

		pokeylogger.debug('\tLocated {!s} {}'.format(acct_count, 'Account(s)'))
		pokeylogger.debug('\tWith : {!s} {}'.format(buddy_count,'Buddies'))
		
	except Exception as e:
		if logging.getLogger().getEffectiveLevel() != logging.DEBUG:
			nf_win = InfoDialog(self, "Error", 'Details : {:}'.format(*e))
			response = nf_win.run()
			nf_win.destroy()
		pokeylogger.error('[*] Details - {:}'.format(*e))
	
def pc_main(**kwargs):
	
	if kwargs is not None:
		
		# Build the list of buddies to send to	
		if 'list' in kwargs:
			lines = [line.strip() for line in open(PASS_LIST)]
			with open(PASS_LIST, "r") as passlist:
				lines = [line.strip() for line in passlist]
			passlist.close()
		
		# Add a specified buddy to the list	
		if 'buddy' in kwargs:
			for name, value in kwargs.items():
				if name=='buddy': lines.append(value)
		
		# Send the message to the list of buddies
		if ('buddy' in kwargs or 'list' in kwargs):
			for name, value in kwargs.items():
				if name=='chats': chat_count=value
			for name, value in kwargs.items():
				if name=='list': pc_pass_req(chat_count, lines)
		
#******************************/PASS_CHATS****************************** 
