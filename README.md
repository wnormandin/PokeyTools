## pokeytools - Installation and Basic Usage

## To Install pokeytools:
### Run the following in your desired installation location (the pokeytools folder will be created in this directory):

```
git clone https://github.com/wnormandin/pokeytools.git
cd pokeytools
ls
```
The tool files and folders will be downloaded, and the location will be connected to the repository for easy updates
You should see (barring any ls aliases):

``` 
 .  ..  .git  .gitignore  pokeytools.py  __init__.py  lib  README.md  tmp
```

Once you see the files listed, to execute run the following command :

``` 
python pokeytools.py
``` 

Logging is set to logging.DEBUG by default
last_run.log will contain the current log or last run if not in the Gtk main loop

## Usage

Pass (LibPurple Messaging Utility)
Use the list of users to manage who will receive your message.
Select a chat count and click "Broadcast" to send your message to the recipients on your list
*Custom Message Functionality to come

### Log Search
Set the search criteria :
- # of Months OR Date (if a date is present, # of Months is ignored)
- Keyword(s) spaces should be ok but single word terms yield broader results
- Specify a Chat Room or User name (Or Both)

Click "Search" and the results will be shown in a browser window

## Search Predefines
Enter a Search Term
Select the Destination:
- XSel(Mouse) : Sends the result to the middle mouse click or X-Selection
- Clipboard : Sends the result to the Gtk Clipboard (Ctrl+V)

Select the result format:
- Text : The selected predefined text will be sent as text
- Pastebin URL : The selected predefined text will be converted to a Pastebin.com Raw URL

Click "Predefine Search"
Matches will show up in a popup window
Select your choice and click "OK" to return the text to your specified destination


