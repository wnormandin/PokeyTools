#!/usr/bin/env python

import dbus, dbus.glib, dbus.decorators, gobject, argparse, sys

DOM_SUFFIX='@openfire.houston.hostgator.com'
PURPLE_CONV_TYPE_IM=1
PASS_LIST='./list.txt'

#****************************BEGIN MAIN*********************************

def main():
	
	parser = argparse.ArgumentParser()
	
	parser.add_argument("-c", "--chats", 
							help="Specify A quantity of passchats")
	parser.add_argument("-b", "--buddy", 
							help="Specify A User to Message")
	parser.add_argument("-a", "--add",
							help="Add a User (by LDAP) to list.txt")
	parser.add_argument("-l", "--list", action="store_true",
							help="Message all users in list.txt")
	parser.add_argument("-s", "--show", action="store_true", 
							help="Show list.txt contents")
	parser.add_argument("-r", "--remove", action="store_true", 
							help="Remove a user from list.txt")
	parser.add_argument("-d", "--dbg", action="store_true",
							help="Turn on Debugging messages")
	parser.add_argument("-t", "--test", action="store_true",
							help="Run Test")

	args = parser.parse_args()
	lines = []
		
	if args.test:
		do_test(args.dbg)
		sys.exit(2)
		
	if args.show:
		
		if args.dbg:
			print "\n[*] Opening list.txt"
			
		with open(PASS_LIST, "r") as passlist:
			lines = [line.strip() for line in passlist]
		passlist.close()
		
		if args.dbg:
			print "\n[*] list.txt Contents :"
			
		for line in lines:
			print "\t" + line
			
		sys.exit(2)
		
	if args.add!=None:
		with open(PASS_LIST, "a") as passlist:
			passlist.write(args.add + "\n")
		passlist.close()
		sys.exit(2)
		
	if args.remove:
		slctn=-1
		with open(PASS_LIST, "r") as passlist:
			lines = [line.strip() for line in passlist]
		passlist.close()
		
		for idx, val in enumerate(lines):
			print str((idx+1)) + ". " + val
		
		while slctn not in range(0, len(lines)+1):
			slctn = input("Choose a line to remove : ")
		
		slctn -= 1
		
		with open(PASS_LIST, "w") as passlist:
			for idx, val in enumerate(lines):
				if idx!=slctn:
					passlist.write(val + "\n")
		
		passlist.close()
		sys.exit(2)
		
	if args.list:
		lines = [line.strip() for line in open(PASS_LIST)]
		with open(PASS_LIST, "r") as passlist:
			lines = [line.strip() for line in passlist]
		passlist.close()
		
	if args.buddy!=None:
		lines.append(args.buddy)
		
	if (args.chats<="0" or args.chats==None):
		print "\nYou must specify a valid number of chats"
		print "\tYou specified : " + str(args.chats)
		sys.exit(2)
		
	if (args.chats>0 and (args.buddy != None or args.list)):
		pass_req(args.chats, lines, args.dbg)
	
#****************************END MAIN***********************************

#*************************BEGIN FUNCTIONS*******************************

def do_test(dbg):
	
	buddy_count = 0
	acct_count = 0
	
	print "\n[*] Testing dBus connection"
	
	bus = dbus.SessionBus()
	obj = bus.get_object("im.pidgin.purple.PurpleService", 
						"/im/pidgin/purple/PurpleObject")
	purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")
	
	print "Success..."
	print "\n[*] Checking for available Pidgin Buddies"
	
	for account in purple.PurpleAccountsGetAllActive():
		for buddy in purple.PurpleFindBuddies(account, ''):
			buddy_count += 1
		
		acct_count += 1
		
	print "Success...\n"

	print "Located " + str(acct_count) + " Account(s)"
	print "With : " + str(buddy_count) + " Buddies"
	
def pass_req(chats, lines, dbg):
	
	ex_flag=False

	if dbg:
		print "\n[*] Testing dBus connection"

	bus = dbus.SessionBus()
	obj = bus.get_object("im.pidgin.purple.PurpleService", 
						"/im/pidgin/purple/PurpleObject")
	purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")
	
	if dbg:
		print "\n[*] Finding Pidgin Accounts"
	
	for acct in purple.PurpleAccountsGetAllActive():
		
		for line in lines:
			
			if dbg:
				print "Pidgin Acct : " + str(acct)
				print "\n[*] Finding Pidgin Buddy : " + line
			
			for buddy in purple.PurpleFindBuddies(acct, ''):
				
				if ex_flag:
					exit
				else:
					buddy_name = purple.PurpleBuddyGetName(buddy)
					
					if buddy_name==line+DOM_SUFFIX:
						
						if dbg:
							print "Buddy Found"
							print "\n[*] Attempting to message user\n\t" + buddy_name
							
						conv = purple.PurpleConversationNew(1, acct, buddy_name)
						im = purple.PurpleConvIm(conv)
						purple.PurpleConvImSend(im, build_msg(str(chats), dbg))
						
						if dbg:
							print "\n[*] Message Sent " + buddy_name
						
						ex_flag=True
				
	
def build_msg(opt, dbg):
	msg = "\nCurrently I have : " + opt + " chats to pass.\nPlease reply if you can assist!\n"
	msg = msg + "\n[*] This has been an automated chat pass request."
	return msg

#*************************END FUNCTIONS*********************************
        
if __name__ == '__main__':
	main()
