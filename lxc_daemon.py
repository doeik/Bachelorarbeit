from __future__ import unicode_literals
import base64
import grp
import io
import json
import lxc
import optparse
import os
import random
import setproctitle
import socket
import stat
import string
import subprocess
import threading
import traceback

LXC_PATH = "/var/lib/lxc/"
TIMEOUT = 30
CONFIG_TEMPLATE = "./config"
UDS_SOCKET = "./uds_lxcdaemon"


def makeConfigFromTemplate(tmpName):
    container_path = os.path.join(LXC_PATH, tmpName) + "/"
    with io.open(CONFIG_TEMPLATE, "r") as config:
        content = config.readlines()
    for i, line in enumerate(content):
        line = line.replace("{container}", container_path)
        line = line.replace("{name}", tmpName)
        content[i] = line
    with io.open(container_path + "config", "w") as newconf:
        for line in content:
            newconf.write(line)


def timerEvent(timeout_event, container):
    timeout_event.set()
    container.stop()


def processLxc(request, program):
    params = request["params"]
    info = None
    timeout = request.get("timeout", TIMEOUT)
    tmpName = "".join([random.choice(string.ascii_letters + string.digits)
                       for n in range(12)])
    container = lxc.Container(tmpName)
    container.create("debian", lxc.LXC_CREATE_QUIET)
    try:
        # makeConfigFromTemplate(tmpName)
        container.start()
        timeout_event = threading.Event()
        t = threading.Timer(timeout, timerEvent, (timeout_event, container))
        t.start()
        prog_path = os.path.join(
            LXC_PATH, tmpName, "rootfs/", os.path.basename(params[0]))
        with io.open(prog_path, "wb") as fi_prog:
            fi_prog.write(program)
        os.chmod(prog_path, stat.S_IEXEC)
        params[0] = os.path.join("/", os.path.basename(params[0]))
        returncode = container.attach_wait(
            lxc.attach_run_command, params, attach_flags=lxc.LXC_ATTACH_DROP_CAPABILITIES, extra_env_vars=("PATH=/bin:/sbin:/usr/bin:/usr/sbin", ))
    except Exception:
        returncode = 2
        info = traceback.format_exc()
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
    return (returncode, timeout_event.is_set(), info)


def handleRunProgAction(request):
    program = base64.b64decode(request["b64_data"].encode("utf8"))
    (returncode, timeout_occured, info) = processLxc(request, program)
    response = {
        "success": True,
        "timeout": timeout_occured,
        "returncode": returncode % 255,
    }
    if info != None:
        response["success"] = False
        response[
            "info"] = "an unexpected exception occured while trying to run the container:\n" + info
    return response


"""
    Insert new actions here.
    Please stick to the following sheme for these methods:
    - takes request dictionary
    - returns new response dictionary

    Method must be referenced in determineMethodFromAction.
"""


def determineMethodFromAction(actionValue):
    return {
        "run_prog": handleRunProgAction,
    }.get(actionValue,
          lambda request: {"success": False,
                           "info": "No such action: " + request.get("action", "None"),
                           })


def handleClient(client_socket):
    fd = client_socket.makefile("rw")
    keep_alive = True
    while keep_alive:
        jsondict = fd.readline()
        try:
            request = json.loads(jsondict)
        except ValueError:
            response = {"success": False,
                        "info": "invalid json object",
                        }
            fd.write(json.dumps(response) + "\n")
            fd.flush()
            break
        else:
            keep_alive = request.get("keep-alive", False)
            method = determineMethodFromAction(
                request.get("action", "None"))
            response = method(request)
            fd.write(json.dumps(response) + "\n")
            fd.flush()
    fd.close()
    client_socket.close()


def runServer():
    setproctitle.setproctitle("lxc_daemon")
    #os.setgid(grp.getgrnam("info2_containers").gr_gid)
    try:
        os.unlink(UDS_SOCKET)
    except OSError:
        pass
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(UDS_SOCKET)
    os.chmod(UDS_SOCKET, stat.S_IRWXU | stat.S_IRGRP | stat.S_IWGRP)
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
            runServer()
        else:
            os._exit(0)
    else:
        os._exit(0)


def main():
    parser = optparse.OptionParser()
    parser.add_option("-b", "--background", action="store_true",
                      dest="background", help="start this process in the background")
    parser.add_option("-s", "--stop", action="store_true",
                      dest="stop", help="terminate all running lxc_daemon processes")
    parser.add_option("-k", "--kill", action="store_true",
                      dest="kill", help="forcibly kill all running lxc_daemon processes")
    (options, args) = parser.parse_args()
    if options.stop:
        subprocess.call(["killall", "lxc_daemon"])
        return
    if options.kill:
        subprocess.call(["killall", "-9", "lxc_daemon"])
        return
    if options.background:
        sendToBackground()
    else:
        runServer()

if __name__ == "__main__":
    main()
