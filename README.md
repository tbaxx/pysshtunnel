pysshtunnel
=========
Open ssh tunnels in Python using with statements.


Dependencies:
- [paramiko](https://pypi.python.org/pypi/paramiko) SSH2 protocol library


Example:
```
from pysshtunnel import SSHTunnel

with SSHTunnel(('192.168.2.10', 22), ('localhost', 8080), 80, 'user', 'pass'):
    print 'Tunnel Is Open'
    # do stuff
print 'Tunnel is Closed'
```
