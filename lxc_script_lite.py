from __future__ import unicode_literals
import subprocess
import sys
import os
import io
import shutil
import random
import string
import threading

LXC_PATH = "/var/lib/lxc/"
TIMEOUT = 30


def writeFile(path, text):
    fobj = io.open(path, 'w')
    fobj.write(text)
    fobj.close()


def makeConfigFromTemplate(tmpName):
    container_path = os.path.join(LXC_PATH, tmpName) + "/"
    config = io.open('./config', 'r')
    content = config.readlines()
    config.close()
    for i, line in enumerate(content):
        line = line.replace("{container}", container_path)
        line = line.replace("{name}", tmpName)
        content[i] = line
    newconf = io.open(container_path + 'config', 'w')
    for line in content:
        newconf.write(line)
    newconf.close()


def main():
    if len(sys.argv) < 2:
        print("Specify a program you want to run inside lxc.")
        exit(1)
    program = sys.argv[1]
    # Generate random string for naming the temporarely created container
    tmpName = ''.join([random.choice(string.ascii_letters + string.digits)
                       for n in range(12)])
    subprocess.call(["lxc-create", "-n", tmpName, "-t", "debian"])

    def timerEvent():
        subprocess.call(["lxc-stop", "-n", tmpName, "-k"])
    try:
        makeConfigFromTemplate(tmpName)
        t = threading.Timer(TIMEOUT, timerEvent)
        t.start()
        rootpath = os.path.join(LXC_PATH, tmpName, "rootfs/")
        shutil.copy(program, rootpath)
        returncode = subprocess.call(
            ["lxc-start", "-n", tmpName, os.path.join("/", program)])
        print("Returncode: " + str(returncode))
    except Exception as e:
        print(e)
    finally:
        try:
            t.cancel()
        except Exception as e:
            print(e)
        subprocess.call(["lxc-destroy", "-n", tmpName])

if __name__ == '__main__':
    main()
