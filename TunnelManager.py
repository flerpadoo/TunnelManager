# Python SSH Tunnel Management Service
# Crimson Development Services - 2016

# You will need to install psutil. If it weren't for windows
# it would be handled with an internal module. Thanks Bill.

# Imports
import datetime, os, psutil, readline, subprocess, sys, threading, time, Tkinter

# Version info for updater script use
ServiceVersion = '1.0.11'

# Service management stuff
# Verbosity enabled will allow all messages with status 1 to print
# Standard output print messages marked with a status 0
# Set production to False if you want to import as a library
isHeadless = True
outputEnabled = True
verboseOutput = False
production = True

# Other global variables
isConnected = False
activeConnections = None
keepAliveInterval = 5  # in minutes
refreshInterval = 20  # in minutes
keepAliveKill = False
refresherKill = False
sleepMonitorKill = False

# Loads the config file
CONFIG_SETTINGS = []
configFile = 'TunnelManager.config'
execfile(configFile)

# The help message
helpMSG = """The current options are as follows:
    \nconnect\t\tconnects to all of the hosts in your config file, and establishes all respective tunnels
    \nsummary\t\tprints the connection summary, which shows information on all active connections
    \ntunnels\t\tlists out all of the active tunnels being managed by this service
    \ndisconnectall\tdisconnects all active connections and their respective tunnels
    \nmonitor\t\toptions for the process monitoring module, which will monitor the PID of ssh connections and reconnect if needed
      start\t\tstarts the process monitor in a backgrounded thread
      stop\t\tstops the process monitor, but does not close any connections
    \nrefresher\toptions for the tunnel refresher module, which reconnects all active SSH sessions
      start\t\tstarts the refresher module in a background thread
      stop\t\tstops the refresher module
    \nverbose\t\toptions to enable verbose output
      true\t\tenables verbose output, allowing the user to see actual SSH commands, full errors, etc
      false\t\tthe default option - disables verbose output for a cleaner console experience
    \nexit\t\tclose all connections, exit the console, and shut down the tunnel manager
    \nhelp\t\tprints out the help message (this message)
    """

# Output control module
def printMsg(messageText, messageType, isLogged):
    if isLogged is True:
        f = open('TunnelManager.log', 'a')
        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        f.write(st + ': ' + messageText + '\n')
        f.close()
    if outputEnabled is True:
        if messageType == 0:
            print('[+] ' + messageText)
        if verboseOutput is True and messageType == 1:
            print('[!] ' + messageText + '\n')

# Command processing module for the console.
def processInput(userInput):
    try:
        userInput = userInput.split(' ')
        if userInput[0] == "connect":
            global tm
            tm = TunnelManager()
            tm.initSSH()
            return
        if userInput[0] == "summary":
            tm.printSummary()
            return
        if userInput[0] == "tunnels":
            tm.printTunnels()
            return
        if userInput[0] == "disconnect":
            tm.killAllSessions()
            return
        if userInput[0] == "reconnect":
            tm.killAllSessions()
            time.sleep(1)
            tm.initSSH()
            return
        if userInput[0] == "monitor":
            if userInput[1] == "start":
                startProcessMonitor(tm)
                return
            if userInput[1] == "stop":
                global keepAliveKill
                keepAliveKill = True
                return
        if userInput[0] == "verbose":
            global verboseOutput
            if userInput[1] == "true":
                verboseOutput = True
                printMsg('Verbose output has been enabled', 0, False)
                return
            if userInput[1] == "false":
                verboseOutput = False
                printMsg('Verbose output has been disabled', 0, False)
                return
        if userInput[0] == "refresher":
            if userInput[1] == "start":
                startTunnelRefresher()
                printMsg("Tunnel Refresher has been started", 0, True)
                return
            if userInput[1] == "stop":
                global refresherKill
                refresherKill = True
                return
        if userInput[0] == "sleepmonitor":
            if userInput[1] == "start":
                startSystemSleepMonitor()
                printMsg('System Sleep Monitor has been started', 0, True)
                return
            if userInput[1] == "stop":
                global sleepMonitorKill
                sleepMonitorKill = True
                return
        if userInput[0] == "exit":
            try:
                tm.killAllSessions()
            except:
                pass
            sys.exit()
        if userInput[0] == "help":
            print(helpMSG)
            return
        else:
            print ' '.join(userInput) + ": Not a command"
            return
    except SystemExit:
        sys.exit('Goodbye!')
    except:
        printMsg("Unexpected error: " + str(sys.exc_info()[0]), 1, True)
        printMsg(str(sys.exc_info()[1:]), 1, True)
        return

# Sets the prompt string and starts the console.
def launchConsole():
    print("Starting the console...\n")
    while 1:
        try:
            promptString = "TunnelManager ~> "
            userInput = raw_input(promptString)
            if userInput != '':
                processInput(str(userInput))
        except KeyboardInterrupt:
            print('\n')

# SSH Tunnel Management Class
class TunnelManager():
    # Default properties and values
    def __init__(self):
        self.connected = False
        self.lastLogin = 'Never'
        self.currentHosts = []
        self.currentTunnels = []
        self.activeConnections = []
        self.baseCmd = ''
        self.lastCheckedTime = None
        # Kills a process given its PID
    def killProcess(pid):
        printMsg('Killing connection with PID ' + pid, 0, True)
        os.kill(pid)
        # Prints a summary of all tunnels currently active
    def systemSleepMonitor(self):
        while sleepMonitorKill is False:
            time.sleep(8)
            if self.lastCheckedTime is not None:
                newTime = datetime.datetime.fromtimestamp(time.mktime(time.gmtime()))
                timeDiff = datetime.timedelta.total_seconds(newTime - self.lastCheckedTime)
                if timeDiff > 10:
                    self.killAllSessions()
                    self.initSSH()
            if self.lastCheckedTime is None:
                self.lastCheckedTime = datetime.datetime.fromtimestamp(time.mktime(time.gmtime()))
            self.lastCheckedTime = datetime.datetime.fromtimestamp(time.mktime(time.gmtime()))
        printMsg('System Sleep Monitor has been stopped.', 0, True)
    def printTunnels(self):
        print('')
        for connection in self.activeConnections:
            address = connection[4]
            connectionID = str(connection[6])
            printMsg('Showing tunnels for connection ID ' + connectionID + ' (Host: ' + address + ')', 0, False)
            print '\n' + '\n'.join(connection[5]) + '\n'
    # Refreshes all SSH connections
    def refreshConnections(self):
        while refresherKill is False:
            time.sleep(refreshInterval * 60)
            printMsg('Refreshing Tunnels...', 0, True)
            self.killAllSessions()
            self.initSSH()
    # Reconnect a session that died off
    def reconnectSSH(self, connection):
        identity = connection[2]
        username = connection[3]
        address = connection[4]
        tunnels = connection[5]
        connectionID = connection[6]
        commandList = ['ssh', '-N', '-i', identity, username + '@' + address]
        for tunnel in tunnels:
            commandList.append(tunnel)
        printMsg('SSH Command for ' + address + ': ' + ' '.join(commandList), 1)
        sshProcess = subprocess.Popen(commandList, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)
        printMsg('Connected to SSH on host ' + address, 0, True)
        self.activeConnections.append([sshProcess, sshProcess.pid, identity, username, address, tunnels, connectionID])
    # Monitors the SSH processes and restarts a connection that has dropped
    def monitorProcesses(self):
        printMsg("Starting process monitor\n", 0, True)
        while keepAliveKill is False:
            time.sleep(keepAliveInterval * 60)
            for activeConnection in self.activeConnections:
                pid = activeConnection[1]
                connectionID = activeConnection[6]
                if psutil.pid_exists(pid) is True:
                    printMsg('Connection with ID of ' + str(connectionID) + ' (PID ' + str(pid) + ') is still active.', 1, False)
                if psutil.pid_exists(pid) is False:
                    printMsg('Connection with ID of ' + str(connectionID) + ' (PID ' + str(pid) + ') is no longer active.\nRestarting...', 0, False)
                    self.reconnectSSH(activeConnection)
    # Sends a keepalive signal to each connected host
    def printSummary(self):
        print("\nActive Connections")
        print("==================")
        for activeConnection in self.activeConnections:
            # process = activeConnection[0]
            pid = activeConnection[1]
            identity = activeConnection[2]
            username = activeConnection[3]
            address = activeConnection[4]
            # tunnels = activeConnection[5]
            connectionID = activeConnection[6]
            print("\nConn. ID: %s\nHost: %s\nUser: %s\nKey: %s\nPID: %s") % (connectionID, address, username, identity, pid)
        print('\n')
    # Initializes an SSH connection for each host in the config file
    def initSSH(self):
        connectionID = 0
        for SSH_DICT in CONFIG_SETTINGS:
            connectionID = connectionID + 1
            identity = SSH_DICT['IDENTITY']
            username = SSH_DICT['USERNAME']
            address = SSH_DICT['ADDRESS']
            tunnels = SSH_DICT['TUNNELS']
            commandList = ['ssh', '-N', '-i', identity, username + '@' + address]
            for tunnel in tunnels:
                commandList.append(tunnel)
            printMsg('SSH Command for ' + address + ': ' + ' '.join(commandList), 1, False)
            sshProcess = subprocess.Popen(commandList, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)
            printMsg('Connected to SSH on host ' + address + ' (PID ' + str(sshProcess.pid) + ')', 0, True)
            self.activeConnections.append([sshProcess, sshProcess.pid, identity, username, address, tunnels, connectionID])
        self.connected = True
    def killAllSessions(self):
        for connection in self.activeConnections:
            printMsg('Closing connection to host ' + str(connection[4]) + " (PID " + str(connection[1]) + ")", 0, True)
            connection[0].terminate()
        self.activeConnections = []
        time.sleep(1)

# Runs the process monitoring module within the TunnelManager class.
# Likely not needed if you are utilizing the tunnel refresher instead.
class startProcessMonitor(object):
    def __init__(self, interval=1):
        self.interval = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()
    def run(self):
        tm.monitorProcesses()
# Runs the tunnel refresher module within the TunnelManager class
class startTunnelRefresher(object):
    def __init__(self, interval=1):
        self.interval = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()
    def run(self):
        tm.refreshConnections()
# Runs the tunnel refresher module within the TunnelManager class
class startSystemSleepMonitor(object):
    def __init__(self, interval=1):
        self.interval = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()
    def run(self):
        tm.systemSleepMonitor()

# Main modules - only work if production is True.
# If production is false, you're probably working
# with it directly in IDLE, like so:
#
#   import TunnelManager as t; tm = t.TunnelManager()
#   tm.initSSH(); tm.printSummary(); tm.monitorProcesses()
#
# The headed main module is to be used if you require a
# compiled executable (or .app for OSX) complete with a UI
#
# The headless main module is to be used if you are not
# going to be using the UI, which has no functonality anyways
#
# This is set up so that OSX users can set up the .app
# to launch at startup, rather than having to mess with
# the plist's and other fun stuff that rarely works right
# the first time.
#
# To force one or the other, modify the isHeadless variable
# at the top of this file. It is headless by default, as
# most users prefer to use the console over having a UI

def mainHeadless():
    if len(sys.argv) < 2:
        printMsg("You must use the '--console' flag if you wish to use this service interactively.", 0, False)
        printMsg("Initiating the SSH connections and starting the refresher service.", 0, False)
        global tm
        tm = TunnelManager()
        tm.initSSH()
        tm.refreshConnections()

# TKinter-related stuff from here on out, for you GUI folks.
def mainHeaded():
    global tm
    tm = TunnelManager()
    tm.initSSH()
    tm.startTunnelRefresher()

# "Connect / Connected" button press: runs the main module for headed version
def connectButton_Press(b):
    if isConnected is False:
        mainHeaded()
        b.config(text="Connected")
    if isConnected is True:
        tm.killAllSessions()
        b.config(text="Connect")

def launchGUI():
    if production is True:
        if isHeadless is False:
            rootWindow = Tkinter.Tk()
            rootWindow.title("TunnelManager " + ServiceVersion)
            rootWindow.resizable(width=False, height=False)
            rootWindow.geometry('{}x{}'.format(500, 200))
            btn_text = Tkinter.StringVar()
            b = Tkinter.Button(rootWindow, command=lambda: connectButton_Press(b), text=btn_text)
            b.pack()
            b.config(text="Connect")
            rootWindow.mainloop()

currentlyAvailableCommands = [
    "--headlessmode",
    "--gui",
    "--console",
    "--silent",
    "--verbose",
    "--refresh",
    "--keepalive",
    "--config"
]

def main():
    global isHeadless
    global verboseOutput
    global outputEnabled
    if len(sys.argv) >= 2:
        cliArguments = sys.argv
        commandsUsed = [i for i in currentlyAvailableCommands if i in cliArguments]
        for command in commandsUsed:
            if command == "--gui":
                isHeadless = False
                launchGUI()
            if command == "--console":
                launchConsole()
            if command == "--silent":
                verboseOutput = False
                outputEnabled = False
            if command == "--refresh":
                tm.startTunnelRefresher()
    if len(sys.argv) < 2:
        mainHeadless()

main()
