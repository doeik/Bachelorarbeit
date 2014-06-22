from __future__ import unicode_literals
import io
import json
import optparse
import os
import random
import shutil
import socket
import string
import subprocess
import threading

LXC_PATH = "/var/lib/lxc/"
TIMEOUT = 30
CONFIG_TEMPLATE = "./config"
SERVER_ADDRESS = "./uds_lxcdaemon"


def makeConfigFromTemplate(tmpName):
    container_path = os.path.join(LXC_PATH, tmpName) + "/"
    config = io.open(CONFIG_TEMPLATE, "r")
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


def timerEvent(timeout_event, tmpName):
        subprocess.call(["lxc-stop", "-n", tmpName, "-k"])
        timeout_event.set()


def processLxc(params):
    program_abspath = params[0]
    program = os.path.basename(program_abspath)
    # Generate random string for naming the temporarely created container
    # TO DO: tempfile
    tmpName = ''.join([random.choice(string.ascii_letters + string.digits)
                       for n in range(12)])
    subprocess.call(["lxc-create", "-n", tmpName, "-t", "debian"])
    timeout_event = threading.Event()
    try:
        makeConfigFromTemplate(tmpName)
        t = threading.Timer(TIMEOUT, timerEvent, (timeout_event, tmpName))
        t.start()
        rootpath = os.path.join(LXC_PATH, tmpName, "rootfs/")
        shutil.copy(program_abspath, rootpath)
        callparams = ["lxc-start", "-n", tmpName,
                      os.path.join("/", program), "-q"]
        callparams.extend(params[1:])
        returncode = subprocess.call(callparams)
    except Exception as e:
        returncode = 2
        print(e)
    finally:
        try:
            t.cancel()
        except:
            pass
        subprocess.call(["lxc-destroy", "-n", tmpName])
    return (returncode, timeout_event.is_set())


def composeReplyToClient(client_socket):
    fd = client_socket.makefile("r")
    jsonlist = fd.readline()
    fd.close()
    try:
        params = json.loads(jsonlist)
    except ValueError as e:
        msg = "invalid json object"
        print(e)
    else:
        (returncode, timeout_occured) = processLxc(params)
        msg = str(returncode)
        if timeout_occured:
            msg = "t/o"
        if returncode == 2:
            msg = "2 - an unexpected exception occured while trying to run the container"
    try:
        client_socket.sendall(msg.encode())
    except Exception as e:
        print(e)
    client_socket.close()


def runServer():
    try:
        os.unlink(SERVER_ADDRESS)
    except OSError:
        pass
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(1)
    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(
            target=composeReplyToClient, args=(client_socket, ))
        client_thread.start()


def sendToBackground():
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
    parser = optparse.OptionParser()
    parser.add_option("-b", "--background", action="store_true",
                      dest="background", help="start this process in the background")
    parser.add_option("-f", "--foreground", action="store_true",
                      dest="foreground", default=True, help="start this process in the foreground")
    (options, args) = parser.parse_args()
    if options.background:
        sendToBackground()
    if options.foreground:
        runServer()

if __name__ == "__main__":
    main()
