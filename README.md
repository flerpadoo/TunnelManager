# TunnelManager
A python-based SSH tunnel management service for those who refuse to leave all of their services accessible to everyone on the Internet, but don't want to use VPNs.

## The Config File
The configuration file for TunnelManager is really quite simple: It is merely a list of dictionaries. Each dictionary contains four pieces of information:

+ ADDRESS
+ USERNAME
+ IDENTITY
+ TUNNELS

TunnelManager uses this list of dictionaries, and connects to each of the host addresses using their respective username and identity files provided in the config file, and establishes the SSH tunnels you specify in the TUNNELS key. Here is an example of a config file with a single host and only a few tunnels:

```python
CONFIG_SETTINGS = [
    {   # My Jumpbox
        "ADDRESS": "jumpbox.yourdomain.com",
        "USERNAME": "username",
        "IDENTITY": "/home/username/.ssh/id_rsa",
        "TUNNELS": ["-L2265:117.39.2.233:22", "-L2264:62.23.1.15:22", "-L2266:92.24.18.52:22", "-D8888"]
    }
]
```

## Usage (IDLE and Command Line)

    p = TunnelManager()
    p.initSSH()
    p.keepAlive()

### This readme is still a work in progress...
