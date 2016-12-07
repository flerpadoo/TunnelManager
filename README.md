** NOTE: This is currently tailored for Unix/Linux while most of the core features are implemented, and the UI is started. The end goal is to be completely cross-platform, and capable of of being fully integrated into other solutions. Presently, the only thing preventing this from being cross-platform is that it uses subprocess to control the ssh client at the cli - we will be moving over to paramiko or similar soon.

# TunnelManager
A python-based SSH tunnel management service for those who refuse to leave all of their services accessible to everyone on the Internet, but don't want to use VPNs. 

### The Config File
The configuration file for TunnelManager is really quite simple: It is merely a list of dictionaries. Each dictionary contains four pieces of information:

+ ADDRESS
+ USERNAME
+ IDENTITY
+ TUNNELS

TunnelManager uses this list of dictionaries, and connects to each of the host addresses using their respective username and identity files provided in the config file, and establishes the SSH tunnels you specify in the TUNNELS key. Here is an example of a config file with a single host and only a few tunnels:

```
CONFIG_SETTINGS = [
    {   # My Jumpbox
        "ADDRESS": "jumpbox.yourdomain.com",
        "USERNAME": "username",
        "IDENTITY": "/home/username/.ssh/id_rsa",
        "TUNNELS": ["-L2265:117.39.2.233:22", "-L2264:62.23.1.15:22", "-L2266:92.24.18.52:22", "-D8888"]
    }
]
```

### Using in IDLE
If you wish to use the service as a library, and import it into your own project, or wish to run it from IDLE to act as a console, spawn multiple TunnelManager classes using different config files, then simply change the 'production' variable in TunnelManager.py to "False" - that will prevent any code from running and just let you access the modules once imported

```
import TunnelManager as t
t = TunnelManager()
t.initSSH()
t.printSummary()
t.startTunnelRefresher()
```

### Using the Console
If production is enabled, you have two options: headed, and headless (UI, or no UI). As of right now, the UI really only has a button to connect, but the console is a bit more extensive. To access the console, simply ensure that the 'production' variable is set to 'True' and that the 'isHeadless' variable is set to 'True'. Then you can run the following command:

```
# python TunnelManager.py --console
```

You will then be greeted with the following prompt:

```
[+] Running in headless mode.
Starting the console...

TunnelManager ~>
```

The help message details all of the available functions within the console:

```
TunnelManager ~> help
The current options are as follows:

connect         connects to all of the hosts in your config file, and establishes all respective tunnels

summary         prints the connection summary, which shows information on all active connections

tunnels         lists out all of the active tunnels being managed by this service

disconnectall   disconnects all active connections and their respective tunnels

monitor         options for the process monitoring module, which will monitor the PID of ssh connections and reconnect if needed
      start             starts the process monitor in a backgrounded thread
      stop              stops the process monitor, but does not close any connections

refresher       options for the tunnel refresher module, which reconnects all active SSH sessions
      start             starts the refresher module in a background thread
      stop              stops the refresher module

verbose         options to enable verbose output
      true              enables verbose output, allowing the user to see actual SSH commands, full errors, etc
      false             the default option - disables verbose output for a cleaner console experience

exit            close all connections, exit the console, and shut down the tunnel manager

help            prints out the help message (this message)
```

### Running the TunnelManager straight-up, with no console
If you omit the '--console' flag with production enabled and isHeadless set to True, then you should see the following when launching the TunnelManager.py script:

```
$ python TunnelManager.py
[+] Running in headless mode.
[+] You must use the '--console' flag if you wish to use this service interactively.
[+] Initiating the SSH connections and starting the refresher service.
[+] Connected to SSH on host ssh.test.com
[+] Connected to SSH on host filter.website.org
[+] Connected to SSH on host jumpbox.yourcompany.net
[+] Starting tunnel refresher
```
