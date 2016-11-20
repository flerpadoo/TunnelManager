# Python SSH Tunnel Management Service
# Crimson Development Services - 2016

# You will need to install psutil. If it weren't for windows
# it would be handled with an internal module. Thanks Bill.

# Imports
import subprocess, time, psutil, sys, threading

# Service management stuff
# Verbosity enabled will allow all messages with status 1 to print
# Standard output print messages marked with a status 0
# Set production to False if you want to import as a library
outputEnabled = True
verboseOutput = False
production = True

# Other global variables
activeConnections = None
kill = False

# Loads the config file
CONFIG_SETTINGS = []
configFile = 'TunnelManager.config'
execfile(configFile)

# Kills all SSH sessions, used for startup and keyboard interrupt (CTRL+C)
def killAllSSH():
    print("Killing all SSH processes - eventually this will only kill the specific PIDs of ssh sessions created using this service")
    subprocess.Popen(['killall', 'ssh'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)
    time.sleep(3)

# SSH Tunnel Management Class
class TunnelManager():
    # Default properties and values
    def __init__(self):
        self.connected = False
        self.lastLogin = 'Never'
        self.currentHosts = []
        self.currentTunnels = []
        self.keepAliveInterval = 10
        self.activeConnections = []
        self.baseCmd = ''
    # Output control module
    def printMsg(self, messageText, messageType):
        if outputEnabled is True:
            if messageType == 0:
                print('[+] ' + messageText)
            if verboseOutput is True and messageType == 1:
                print('[!] ' + messageText + '\n')
    def printTunnels(self, activeConnections):
        for connection in activeConnections:
            print ' '.join(connection[5])
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
            self.printMsg('SSH Command for ' + address + ': ' + ' '.join(commandList), 1)
            sshProcess = subprocess.Popen(commandList, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)
            self.printMsg('Connected to SSH on host ' + address, 0)
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
        self.printMsg('SSH Command for ' + address + ': ' + ' '.join(commandList), 1)
        sshProcess = subprocess.Popen(commandList, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)
        self.printMsg('Connected to SSH on host ' + address, 0)
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
    # Monitors the SSH processes and restarts a connection that has dropped
    def monitorProcesses(self):
        self.printMsg("Starting process monitor", 0)
        while kill is False:
            time.sleep(self.keepAliveInterval)
            for activeConnection in self.activeConnections:
                pid = activeConnection[1]
                connectionID = activeConnection[6]
                if psutil.pid_exists(pid) is True:
                    self.printMsg('Connection with ID of ' + str(connectionID) + ' (PID ' + str(pid) + ') is still active.', 1)
                if psutil.pid_exists(pid) is False:
                    self.printMsg('Connection with ID of ' + str(connectionID) + ' (PID ' + str(pid) + ') is no longer active.\nRestarting...', 0)
                    self.reconnectSSH(activeConnection)

class startProcessMonitor(object):
    def __init__(self, interval=1):
        self.interval = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()
    def run(self):
        tm.monitorProcesses()

# Main module: Sets the prompt string and starts the console.
def main():
    print("Starting the console...\n")
    while 1:
        try:
            promptString = "TunnelManager ~> "
            userInput = raw_input(promptString)
            if userInput != '':
                processInput(str(userInput))
        except KeyboardInterrupt:
            print('\n')

# Command processing module for the console.
def processInput(userInput):
    if userInput == "connect":
        global tm
        tm = TunnelManager()
        tm.initSSH()
        return
    if userInput == "summary":
        tm.printSummary()
        return
    if userInput == "tunnels":
        tm.printTunnels()
        return
    if userInput == "disconnect":
        killAllSSH()
        return
    if userInput[0] == "monitor":
        if userInput[1] == "start":
            startProcessMonitor()
        if userInput[1] == "stop":
            global kill
            kill = True
        return
    if userInput == "exit":
        sys.exit('Goodbye!')
    if userInput == "help":
        print "\nThe current options are:\n\tconnect\n\tsummary\n\tmonitor\n\texit"
    else:
        print userInput + ": Not a command"
        return

# Run main() - only works if production is True
# If production is false, you should be working
# with it directly in IDLE, like so:
#
#   import TunnelManager as t; tm = t.TunnelManager()
#   tm.initSSH(); tm.printSummary(); tm.monitorProcesses()
#
if production is True:
    if len(sys.argv) < 2:
        global tm
        tm = TunnelManager()
        tm.initSSH()
        tm.printSummary()
        tm.monitorProcesses()
    if len(sys.argv) > 2:
        if sys.argv[2] == "/console":
            main()
