from xmlrpc.client import ServerProxy, Binary

password = open ('password.txt') .read () .strip ()
server = open ('server.txt') .read () .strip ()
server = ServerProxy (server)

def run (module): server.run_module (password, module)
def kill (module): server.kill_module (password, module)
def install (module, path): server.install_module (password, module, Binary (open (path, 'rb') .read ()))
def running ():
    res = server.running_modules (password)
    if res: return res
    else: return []
