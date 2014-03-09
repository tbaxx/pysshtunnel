import select, SocketServer, threading, sys, traceback
import paramiko


def e2s(e):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    trace = ' -> '.join(['%s:%s' % (f.split('\\')[-1:][0], l)
                         for (f, l, m, c) in traceback.extract_tb(exc_tb)])
    return '%s: %s [%s]' % (type(e).__name__, str(e), trace)


class ForwardServer(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            chan = self.ssh_transport().open_channel\
                ('direct-tcpip', (self.chain_host, self.chain_port),
                 self.request.getpeername())
            try:
                while True:
                    r, w, x = select.select([self.request, chan], [], [])
                    if self.request in r:
                        data = self.request.recv(1024)
                        if len(data) == 0:
                            break
                        chan.send(data)
                    if chan in r:
                        data = chan.recv(1024)
                        if len(data) == 0:
                            break
                        self.request.send(data)
            finally:
                chan.close()
        except Exception, e:
            self.log(e2s(e))
        finally:
            self.request.close()


class SSHTunnelCore(object):

    def __init__(self, server, remote_port, local_port, username, password,
                 key_filename, _log):
        self._log = _log
        self._server = server
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.client = None
        class SubHander(Handler):
            chain_host = remote_port[0]
            chain_port = remote_port[1]
            ssh_transport = self.get_transport
            log = lambda x, y: _log(y)
        self.server = ForwardServer(('', local_port), SubHander)
        self.port = self.server.socket.getsockname()[1]
        self.worker = threading.Thread(target=self.server.serve_forever)
        self.worker.setDaemon(True)
        self.worker.start()

    def get_transport(self):
        if (self.client == None)\
           or (self.client.get_transport() == None)\
           or (not self.client.get_transport().isAlive()):
            if self.client:
                self.client.close()
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
            client.connect(self._server[0], self._server[1], username=self.username,
                           password=self.password, key_filename=self.key_filename)
            self.client = client
        return self.client.get_transport()

    def close(self):
        self.server.shutdown()
        self.worker.join()
        if self.client:
            self.client.close()


class SSHTunnel(object):
    """Dynamically opens ssh tunnels, supporting Python's with statement. Uses paramiko."""

    def __init__(self, server, remote_port, local_port, username, password=None,
                 key_filename=None, log=(lambda x: None)):
        """Class constructor.
        
        Keyword arguments:
        server -- a tuple consisting of the hostname and ssh port of the ssh server
        remote_port -- a tuple consisting of the hostname and port of the tunnel's destination
        local_port -- the port that will be tunneled on the local machine
        username -- the username used to authenticate to the ssh server
        password -- the password used to authenticate to the ssh server (optional)
        key_filename -- the certificate file used to authenticate to the ssh server (optional)
        log -- the function that will be invoked for logging (it must accept a string)
        """        
        self.args = (server, remote_port, local_port, username, password,
                     key_filename, log)
        self.lock = threading.Lock()
        self.counter = 0
        self.port = local_port

    def acquire(self):
        with self.lock:
            if self.counter == 0:
                self.tunnel = SSHTunnelCore(*self.args)
                self.port = self.tunnel.port
            self.counter += 1

    def release(self):
        with self.lock:
            assert self.counter > 0
            self.counter -= 1
            if self.counter == 0:
                self.tunnel.close()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, type, value, traceback):
        self.release()
