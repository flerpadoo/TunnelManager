# TunnelManager
A python-based SSH tunnel management service for those who refuse to leave all of their services accessible to everyone on the Internet, but don't want to use VPNs.

## The Config File
The configuration file for TunnelManager is really quite simple: It is merely a list of dictionaries. Each dictionary contains four pieces of information:

+ ADDRESS
+ USERNAME
+ IDENTITY
+ TUNNELS

