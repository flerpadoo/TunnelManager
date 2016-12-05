# TunnelManager OSX Installer
# Crimson Development 2016

# Downloads the newest version of the TunnelManager and places it in
# /Applications/TunnelManager. It will also download the updater for
# TunnelManager, as well as set up OSX launch control scripts so that
# the TunnelManager solution runs at startup.

# Imports
import datetime, os, sys, time, urllib2

# Global variables
userName = os.getenv("SUDO_USER")
appName = 'TunnelManager'
installPath = '/Applications/TunnelManager/'
outputEnabled = True
verboseOutput = True

# OSX plist template
plistTemplate = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.%s.%s</string>

  <key>Program</key>
  <string>%s%s.py</string>

  <key>RunAtLoad</key>
  <true/>

  <key>StandardErrorPath</key>
  <string>/tmp/com.%s.%s.err</string>

  <key>StandardOutPath</key>
  <string>/tmp/com.%s.%s.out</string>
</dict>
</plist>""" % (userName, appName, installPath, appName, userName, appName, userName, appName)

# OSX bash script that sets permissions and launch control
bashScript = """
sudo chown -R %s /Applications/TunnelManager
sudo chmod 600 /Library/LaunchAgents/com.%s.%s.plist
sudo chown root:wheel /Library/LaunchAgents/com.%s.%s.plist
chmod +x %s%s.py
sudo launchctl load /Library/LaunchAgents/com.%s.%s.plist""" % (userName, userName, appName, userName, appName, installPath, appName, userName, appName)

# Downloads all files associated with TunnelManager and a dictionary with the file contents
def fileDownloader():
        tmConfig = urllib2.urlopen('https://raw.githubusercontent.com/halphen/TunnelManager/master/TunnelManager.config')
        tunnelManagerConfig = tmConfig.read()
        tmScript = urllib2.urlopen('https://raw.githubusercontent.com/halphen/TunnelManager/master/TunnelManager.py')
        tunnelManagerMain = tmScript.read()
        tmUpdater = urllib2.urlopen('https://raw.githubusercontent.com/halphen/TunnelManager/master/TunnelManagerUpdater.py')
        tunnelManagerUpdater = tmUpdater.read()
        fileDict = {'configFile': tunnelManagerConfig, 'mainScript': tunnelManagerMain, 'updaterScript': tunnelManagerUpdater}
        return fileDict

# Creates the install directory if it doesn't already exist, and backs up the config before clearing the directory if it does exist.
def setupInstallDirectories():
    if not os.path.exists(installPath):
        os.makedirs(installPath)
        installDirStatus = {'status': 'fresh'}
        return installDirStatus
    if os.path.exists(installPath):
        originalConfigContents = open(installPath + appName + '.config', 'r').read()
        filelist = [f for f in os.listdir(".") if f.endswith(".bak")]
        for f in filelist:
            os.remove(f)
        installDirStatus = {'status': 'old', 'config': originalConfigContents}
        return installDirStatus

# Places the newly-downloaded files, and uses the existing config file if it exists.
def placeFiles(fileDict, installDirStatus):
        startupPlist = open('/Library/LaunchAgents/com.' + userName + '.' + appName + '.plist', 'w')
        startupPlist.write(plistTemplate)
        startupPlist.close()
        mainScript = open(installPath + appName + '.py', 'w')
        mainScript.write(fileDict['mainScript'])
        mainScript.close()
        updaterScript = open(installPath + appName + 'Updater.py', 'w')
        updaterScript.write(fileDict['updaterScript'])
        updaterScript.close()
        if installDirStatus['status'] == 'old':
            printMsg('Using old config file...', 0, False)
            configFile = open(installPath + appName + '.config', 'w')
            configFile.write(installDirStatus['config'])
            configFile.close()
        if installDirStatus['status'] == 'fresh':
            configFile = open(installPath + appName + '.config', 'w')
            configFile.write(fileDict['configFile'])
            configFile.close()

# Output control module
def printMsg(messageText, messageType, isLogged):
    if isLogged is True:
        f = open('TunnelManager_Installer.log', 'a')
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        f.write(st + ': ' + messageText + '\n')
        f.close()
    if outputEnabled is True:
        if messageType == 0:
            print('[+] ' + messageText)
        if verboseOutput is True and messageType == 1:
            print('[!] ' + messageText + '\n')

# Main module: runs fileDownloader(), setupInstallDirectories(), then placeFiles() before launching TunnelManager
def main():
    try:
        printMsg('Downloading newest TunnelManager files...', 0, False)
        fileDict = fileDownloader()
    except:
        printMsg('Unable to download the newest files for some reason. Please check your Internet connection', 1, False)
        sys.exit()
    printMsg('Creating the install directory...', 0, False)
    installDirStatus = setupInstallDirectories()
    printMsg('Installing required files...', 0, False)
    placeFiles(fileDict, installDirStatus)
    for command in bashScript.split('\n'):
        os.system(command)
    print('Install Complete!')

main()
