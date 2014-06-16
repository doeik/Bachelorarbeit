import sys
import os
import socket
import _thread
import subprocess
import io
import fcntl
import atexit

SERVER_ADDRESS = "./uds_lxcdaemon"
LOCKFILE = "./.lock_lxcdaemon"
FD_LOCK = None
RUNNING = True

def cleanup():
    FD_LOCK.close()
    os.unlink(LOCKFILE)
    os.unlink(SERVER_ADDRESS)


def handleInstance():
    global FD_LOCK
    FD_LOCK = io.open(LOCKFILE, "w")
    try:
        fcntl.flock(FD_LOCK, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        return False
    return True

def handleLxc(params):
    params.insert(0, "lxc_script_lite.py")
    params.insert(0, "python")
    logfile = io.open("./daemontest.txt", "w")
    for line in params:
        logfile.write(line)
    logfile.close()
    subprocess.call(params)


def evaluateMessage(text):
    global RUNNING
    if text[0] == "!":
        RUNNING = False
        return
    params = text[1:].split()
    _thread.start_new_thread(handleLxc, (params, ))


def runServer():
    try:
        os.unlink(SERVER_ADDRESS)
    except OSError:
        pass
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(1)
    while RUNNING:
        toClient_socket, toClient_address = server_socket.accept()
        try:
            tmpstr = toClient_socket.recv(2048)
            evaluateMessage(tmpstr.decode())
        finally:
            toClient_socket.close()


def startDaemon():
    pid = os.fork()
    if pid == 0:
        os.setsid()
        pid = os.fork()
        if pid == 0:
            # os.chdir("/")
            os.umask(0)
            runServer()
        else:
            os._exit(0)
    else:
        os._exit(0)


def main():
    if handleInstance() == True:
        atexit.register(cleanup)
        if len(sys.argv) > 1:
            if sys.argv[1] == "debug":
                runServer()
                return
        startDaemon()

if __name__ == "__main__":
    main()
