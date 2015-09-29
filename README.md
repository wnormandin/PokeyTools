#hgtools_gtk - Installation and Basic Usage

#To Install hgtools_gtk:
##Run the following (in the folder where you desire the repository folder (~/tools):

```
git clone https://github.com/wnormandin/hgtools_gtk.git
cd hgtools_gtk
ls
```
###This will download the project files and create a new repository in the folder for easy updating in the future.
###You should see (barring any ls alias):

``` 
 .  ..  .git  .gitignore  hgtools_gtk.py  __init__.py  lib  README.md  tmp
```

##Once you see the files listed, to execute run the following command :

``` 
python hgtools_gtk.py
``` 
###An automatic installation script will soon be implemented, along with automatic updating upon user login. 
###Logging is set to logging.DEBUG by default
###last_run.log will contain the current log or last run if not in the Gtk main loop

#Usage

##Pass Chats
###Use the list of users to manage who will receive your message.
###Select a chat count and click "Broadcast" to send your message to the recipients on your list
### *Custom Message Functionality to come

##Spark Log Search
###Set the search criteria :
- # of Months OR Date (if a date is present, # of Months is ignored)
- Keyword(s) spaces should be ok but single word terms yield broader results
- Specify a Chat Room or User LDAP (Or Both)

###Click "Search" and the results will be shown in a browser window
### *Search functionality is buggy, still working on the algorithm

##Search Predefines
###Enter a Search Term
###Select the Destination:
- XSel(Mouse) : Sends the result to the middle mouse click or X-Selection
- Clipboard : Sends the result to the Gtk Clipboard (Ctrl+V)

###Select the result format:
- Text : The selected predefined text will be sent as text
- HGFix URL : The selected predefined text will be converted to a HGFix Paste URL

###Click "Predefine Search"
####Matches will show up in a popup window
####Select your choice and click "OK" to return the text to your specified destination


