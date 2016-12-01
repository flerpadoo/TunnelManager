# Python SSH Tunnel Management Service
# Crimson Development Services - 2016

# You will need to install psutil. If it weren't for windows
# it would be handled with an internal module. Thanks Bill.

# Imports
import subprocess, time, psutil, sys, threading, os, Tkinter, datetime

# Version info for updater script use
ServiceVersion = '1.0.11'
UpdaterVersion = '1.0'

# Service management stuff
# Verbosity enabled will allow all messages with status 1 to print
# Standard output print messages marked with a status 0
# Set production to False if you want to import as a library
isHeadless = True
outputEnabled = False
verboseOutput = False
production = True

# Other global variables
activeConnections = None
refreshTunnels = True
keepAliveInterval = 5  # in minutes
refreshInterval = 10  # in minutes
keepAliveKill = False
refresherKill = False

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
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
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
        if userInput[0] == "disconnectall":
            for connection in tm.activeConnections:
                tm.killProcess(connection[1])
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
                return
            if userInput[1] == "stop":
                global refresherKill
                refresherKill = True
                return
        if userInput[0] == "exit":
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
        printMsg("Unexpected error: " + sys.exc_info()[0], 1, True)
        printMsg(sys.exc_info()[1:], 1, True)
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
            printMsg('Connected to SSH on host ' + address, 0, True)
            self.activeConnections.append([sshProcess, sshProcess.pid, identity, username, address, tunnels, connectionID])
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
    # Prints a summary of all tunnels currently active
    def printTunnels(self):
        for connection in self.activeConnections:
            address = connection[4]
            connectionID = str(connection[6])
            print 'Showing tunnels for connection ID ' + connectionID + ' (Host: ' + address + ')'
            print ' '.join(connection[5]) + '\n'
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
    # Refreshes all SSH connections
    def refreshConnections(self):
        printMsg("Starting tunnel refresher", 0, True)
        if refreshTunnels is True:
            while refresherKill is False:
                time.sleep(refreshInterval * 60)
                printMsg('\nRefreshing Tunnels...', 0, True)
                for connection in self.activeConnections:
                    printMsg('Closing connection to host ' + str(connection[4]) + " (PID " + str(connection[1]) + ")", 0, True)
                    connection[0].terminate()
                self.activeConnections = []
                time.sleep(2)
                self.initSSH()
        return
    # Kills a process given its PID
    def killProcess(pid):
        printMsg('Killing connection with PID ' + pid, 0, True)
        os.kill(pid)

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
    if production is True:
        if len(sys.argv) < 2:
            global tm
            tm = TunnelManager()
            tm.initSSH()
            tm.printSummary()
            startTunnelRefresher()
        if len(sys.argv) >= 2:
            if sys.argv[1] == "/console":
                launchConsole()

def mainHeaded():
    global tm
    tm = TunnelManager()
    tm.initSSH()
    startTunnelRefresher()

if isHeadless is True:
    printMsg('Running in headless mode. You must append "/console" to your command if you wish to use in interactive mode.', 0, True)
    mainHeadless()
if isHeadless is False:
    rootWindow = Tkinter.Tk()
    rootWindow.title("TunnelManager " + ServiceVersion)
    mainHeaded()
    rootWindow.mainloop()
