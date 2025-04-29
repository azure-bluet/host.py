# This is a program manager
# Features:
# Launch/stop
# Upgrade (stop if still running)

PORT = 1148

import os
from importlib import import_module
from shutil import rmtree
from socketserver import TCPServer
from ssl import PROTOCOL_TLS_SERVER, SSLContext
from time import sleep
from xmlrpc.client import Binary, ServerProxy
from xmlrpc.server import SimpleXMLRPCDispatcher, SimpleXMLRPCRequestHandler
from zipfile import ZipFile

class SSLServer (TCPServer):

    context = SSLContext (PROTOCOL_TLS_SERVER)
    context.load_cert_chain ("certs/ssl.pem", "certs/ssl.key")

    def get_request(self):
        newsocket, fromaddr = self.socket.accept ()
        connstream = self.context.wrap_socket (newsocket, server_side=True)
        return (connstream, fromaddr)

class SSLXMLRPCServer (SSLServer, SimpleXMLRPCDispatcher):

    allow_reuse_address = True

    def __init__ (self, addr, requestHandler=SimpleXMLRPCRequestHandler,
                  logRequests=True, allow_none=True, encoding=None, bind_and_activate=True):
        
        self.logRequests = logRequests
        SimpleXMLRPCDispatcher.__init__ (self, allow_none, encoding)
        SSLServer.__init__ (self, addr, requestHandler, bind_and_activate)

running = {}

password = open ('password.txt') .read () .strip ()
def Authorized (func):
    def new (pswd: str, *rest):
        if pswd == password:
            res = func (*rest)
            if res is not None: return res
            else: return True
        else: return False
    new.__name__ = func.__name__
    return new
_key = os.urandom (16)
def Internal (func):
    def new (pswd: Binary, *rest):
        if pswd.data == _key:
            res = func (*rest)
            if res is not None: return res
            else: return True
        else: return False
    new.__name__ = func.__name__
    return new
srv = ServerProxy (open ('server.txt') .read () .strip ())
def call_internal (name, *params):
    srv.__getattr__ (name) (Binary (_key), *params)

@Authorized
def run_module (module):
    pid = os.fork ()
    if pid: running [module] = pid
    else:
        try:
            import_module (module)
        except KeyboardInterrupt: pass
        call_internal ('rmr', module)
        os._exit (0)

@Authorized
def kill_module (module):
    if module in running:
        os.kill (running [module], 2)

@Authorized
def install_module (module: str, zipfile: Binary):
    kill_module (password, module)
    sleep (2)
    if os.path.isdir (module): rmtree (module)
    # Cache this zipfile
    zf = open ('temp.zip', 'wb')
    zf.write (zipfile.data)
    zf.close ()
    zipfile: ZipFile = ZipFile ('temp.zip')
    os.mkdir (module)
    zipfile.extractall (module + os.sep)
    zipfile.close ()
    # Installed
    run_module (password, module)

@Authorized
def running_modules ():
    return list (running.keys ())

@Internal
def rmr (module): del running [module]

server = SSLXMLRPCServer (('', PORT))
server.register_function (run_module)
server.register_function (kill_module)
server.register_function (install_module)
server.register_function (running_modules)
server.register_function (rmr)
server.serve_forever ()
