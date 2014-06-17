from __future__ import unicode_literals
import _thread
import atexit
import fcntl
import io
import os
import random
import shutil
import socket
import string
import subprocess
import sys
import threading

LXC_PATH = "/var/lib/lxc/"
TIMEOUT = 30
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


def composeReply(toClient_socket, returncode, timeout_occured):
    if timeout_occured:
        msg = "t/o"
    else:
        msg = str(returncode)
    try:
        toClient_socket.sendall(msg.encode())
    except Exception as e:
        print(e)
    toClient_socket.close()


def makeConfigFromTemplate(tmpName):
    container_path = os.path.join(LXC_PATH, tmpName) + "/"
    config = io.open("./config", "r")
    content = config.readlines()
    config.close()
    for i, line in enumerate(content):
        line = line.replace("{container}", container_path)
        line = line.replace("{name}", tmpName)
        content[i] = line
    newconf = io.open(container_path + "config", "w")
    for line in content:
        newconf.write(line)
    newconf.close()


def handleLxc(toClient_socket, params):
    program_abspath = params[0]
    program = os.path.basename(program_abspath)
    # Generate random string for naming the temporarely created container
    # TO DO: tempfile
    tmpName = ''.join([random.choice(string.ascii_letters + string.digits)
                       for n in range(12)])
    subprocess.call(["lxc-create", "-n", tmpName, "-t", "debian"])
    timeout_occured = False

    def timerEvent():
        subprocess.call(["lxc-stop", "-n", tmpName, "-k"])
        nonlocal timeout_occured
        timeout_occured = True
    try:
        makeConfigFromTemplate(tmpName)
        t = threading.Timer(TIMEOUT, timerEvent)
        t.start()
        rootpath = os.path.join(LXC_PATH, tmpName, "rootfs/")
        shutil.copy(program_abspath, rootpath)
        callparams = ["lxc-start", "-n", tmpName,
                      os.path.join("/", program), "-q"]
        callparams.extend(params[1:])
        returncode = subprocess.call(callparams)
        #print("Returncode: " + str(returncode))
    except Exception as e:
        print(e)
    finally:
        try:
            t.cancel()
        except:
            pass
        composeReply(toClient_socket, returncode, timeout_occured)
        subprocess.call(["lxc-destroy", "-n", tmpName])


def evaluateMessage(toClient_socket, text):
    global RUNNING
    if text[0] == "!":
        RUNNING = False
        msg = "Stopped"
        try:
            toClient_socket.sendall(msg.encode())
        except:
            pass
        return
    params = text[1:].split()
    _thread.start_new_thread(handleLxc, (toClient_socket, params))


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
            evaluateMessage(toClient_socket, tmpstr.decode())
        except:
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
