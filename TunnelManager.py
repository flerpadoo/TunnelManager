# Python SSH Tunnel Management Service
# Crimson Development Services - 2016

# Imports
import subprocess, time

# Output settings
outputEnabled = True
verboseOutput = False

# Loads the config file
CONFIG_SETTINGS = []
configFile = 'TunnelManager.config'
execfile(configFile)

# Kills all SSH sessions, used for startup and keyboard interrupt (CTRL+C)
def killAllSSH():
    subprocess.Popen(['killall', 'ssh'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)
    subprocess.Popen(['killall', 'python'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)

# SSH Tunnel Management Class
class TunnelManager():
    # Default properties and values
    def __init__(self):
        self.connected = False
        self.lastLogin = 'Never'
        self.currentHosts = []
        self.currentTunnels = []
        self.keepAliveInterval = 120
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
        for SSH_DICT in CONFIG_SETTINGS:
            commandList = ['ssh', '-N', '-i', SSH_DICT['IDENTITY'], SSH_DICT['USERNAME'] + '@' + SSH_DICT['ADDRESS']]
            for tunnel in SSH_DICT['TUNNELS']:
                commandList.append(tunnel)
            self.printMsg('SSH Command for ' + SSH_DICT['ADDRESS'] + ': ' + str(commandList), 1)
            sshProcess = subprocess.Popen(commandList, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)
            self.printMsg('Connected to SSH on host ' + SSH_DICT['ADDRESS'], 0)
            self.activeConnections.append(sshProcess)
    # Sends a keepalive singal to each connected host
    def keepAlive(self):
        while True:
            time.sleep(self.keepAliveInterval)
            for sshConnection in self.activeConnections:
                sshConnection.stdin.write("echo KEEPALIVE .\n")
                sshConnection.stdin.write("echo END\n")
            self.printMsg('Sent keepalive messages to all connected hosts', 1)

# Main module: runs the tunnel manager, then keepalive forever
def main():
    killAllSSH()
    print('\n')
    p = TunnelManager()
    p.initSSH()
    p.keepAlive()

# Run main()
try:
    main()
except KeyboardInterrupt:
    print "Closing SSH sessions and exiting"
    killAllSSH()
