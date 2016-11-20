# Python SSH Tunnel Management Service
# Crimson Development Services - 2016

# This script will update the main script, TunnelManager.py but
# does not touch the TunnelManager.config file. If there have
# been changes to the way the configuration file structure, the
# updater will ask if you've taken backups yet. If you do not
# back up your config file, it will be overwritten. As of right
# now, you must transpose the old content to the new file by
# yourself. However, in the future this file will perform the
# migration of your old configuration file to the new structure.
# No updates have been made to the config file since inception,
# so this is not really a priority right now.

# Imports
import urllib2, os

# Global variables
updateURL = "https://raw.githubusercontent.com/halphen/TunnelManager/master/TunnelManager.py"

def getNewTMVersion():
    response = urllib2.urlopen(updateURL)
    pythonCode = response.read()
    return pythonCode

os.remove('TunnelManager.py')
pythonCode = getNewTMVersion()
f = open('TunnelManager.py', "w")
f.write(pythonCode)
f.close()
