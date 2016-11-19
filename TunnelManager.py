# Python SSH Tunnel Management Service
# Crimson Development Services - 2016

# You will need to install psutil. If it weren't for windows
# it would be handled with an internal module. Thanks Bill.

# Imports
import subprocess, time, psutil

# Service management stuff
outputEnabled = False
verboseOutput = False
production = True

# Loads the config file
CONFIG_SETTINGS = []
configFile = 'TunnelManager.config'
execfile(configFile)

# Kills all SSH sessions, used for startup and keyboard interrupt (CTRL+C)
def killAllSSH():
    subprocess.Popen(['killall', 'ssh'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)

# SSH Tunnel Management Class
class TunnelManager():
    # Default properties and values
    def __init__(self):
        self.connected = False
        self.lastLogin = 'Never'
        self.currentHosts = []
        self.currentTunnels = []
        self.keepAliveInterval = 30
        self.activeConnections = []
        self.baseCmd = ''
    # Output control module
    def printMsg(self, messageText, messageType):
        if outputEnabled is True:
            if messageType == 0:
                print('[+] ' + messageText)
            if verboseOutput is True and messageType == 1:
                print('[!] ' + messageText + '\n')
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
        while True:
            time.sleep(self.keepAliveInterval)
            for activeConnection in self.activeConnections:
                pid = activeConnection[1]
                connectionID = activeConnection[6]
                if psutil.pid_exists(pid) is True:
                    self.printMsg('Connection with ID of ' + str(connectionID) + ' (PID ' + str(pid) + ') is still active.', 1)
                if psutil.pid_exists(pid) is False:
                    print('Connection with ID of ' + str(connectionID) + ' (PID ' + str(pid) + ') is no longer active.\nRestarting...')
                    self.reconnectSSH(activeConnection)

# Main module: runs the tunnel manager, then keepalive forever
def main():
    tm = TunnelManager()
    tm.initSSH()
    tm.monitorProcesses()

# Run main() - only works if production is True
# If production is false, you should be working
# with it directly in IDLE, like so:
#
#   import TunnelManager as t; tm = t.TunnelManager()
#   tm.initSSH(); tm.printSummary(); tm.monitorProcesses()
#
if production is True:
    try:
        main()
    except KeyboardInterrupt:
        print "Closing SSH sessions and exiting"
        killAllSSH()
