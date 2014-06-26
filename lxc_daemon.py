from __future__ import unicode_literals
import base64
import io
import json
import lxc
import optparse
import os
import random
import socket
import stat
import string
import subprocess
import threading

LXC_PATH = "/var/lib/lxc/"
TIMEOUT = 10
CONFIG_TEMPLATE = "./config"
UDS_SOCKET = "./uds_lxcdaemon"


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


def timerEvent2(timeout_event, tmpName):
    timeout_event.set()
    bla = io.open("timertest", "w")
    bla.write("test")
    bla.close
    subprocess.call(["lxc-stop", "-n", tmpName, "-k"])


def timerEvent(timeout_event, container):
    timeout_event.set()
    print("Container state: " + container.state)
    container.stop()
    print("Container state: " + container.state)


def processLxc(dict_request, program):
    params = dict_request["params"]
    if "timeout" in dict_request:
        timeout = dict_request["timeout"]
    else:
        timeout = TIMEOUT
    tmpName = "".join([random.choice(string.ascii_letters + string.digits)
                       for n in range(12)])
    container = lxc.Container(tmpName)
    container.create("debian", lxc.LXC_CREATE_QUIET)
    try:
        #makeConfigFromTemplate(tmpName)
        container.start()
        timeout_event = threading.Event()
        t = threading.Timer(timeout, timerEvent2, (timeout_event, tmpName))
        t.start()
        prog_path = os.path.join(
            LXC_PATH, tmpName, "rootfs/", os.path.basename(params[0]))
        fd_prog = io.open(prog_path, "wb")
        fd_prog.write(program)
        fd_prog.close()
        os.chmod(prog_path, stat.S_IEXEC)
        params[0] = os.path.join("/", os.path.basename(params[0]))
        returncode = container.attach_wait(
            lxc.attach_run_command, params, attach_flags=lxc.LXC_ATTACH_DROP_CAPABILITIES, extra_env_vars="PATH=/bin:/sbin:/usr/bin:/usr/sbin")
    except Exception as e:
        returncode = 2
        print(e)
    finally:
        try:
            t.cancel()
        except:
            pass
        if not timeout_event.is_set():
            if not container.shutdown(5):
                container.stop()
        else:
            container.wait("STOPPED", 10)
        container.destroy()
    return (returncode, timeout_event.is_set())


def handleRunProgAction(dict_request):
    program = base64.b64decode(
        dict_request["b64_data"].encode(encoding="utf8"))
    (returncode, timeout_occured) = processLxc(dict_request, program)
    msg = str(returncode % 255)
    if timeout_occured:
        msg = "t/o"
    if returncode == 2:
        msg = "2 - an unexpected exception occured while trying to run the container"
    return msg


def handleClient(client_socket):
    fd = client_socket.makefile("rw")
    keep_alive = True
    while keep_alive:
        jsondict = fd.readline()
        try:
            dict_request = json.loads(jsondict)
        except ValueError:
            fd.write("invalid json object")
            break
        else:
            if "keep-alive" in dict_request:
                keep_alive = dict_request["keep-alive"]
            else:
                keep_alive = False
            if dict_request["action"] == "run_prog":
                response = handleRunProgAction(dict_request)
            fd.write(response + "\n")
            fd.flush()
    fd.close()
    client_socket.close()


def runServer():
    try:
        os.unlink(UDS_SOCKET)
    except OSError:
        pass
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(UDS_SOCKET)
    server_socket.listen(1)
    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(
            target=handleClient, args=(client_socket, ))
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
    (options, args) = parser.parse_args()
    if options.background:
        sendToBackground()
    else:
        runServer()

if __name__ == "__main__":
    main()
