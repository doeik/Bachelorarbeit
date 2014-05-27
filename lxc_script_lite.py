### Variables that may be changed ###

lxc_path = "/var/lib/lxc/"
timeout = 0

### Imports ###

import subprocess
import sys
import shutil
import random
import string

### Function scope ###

def handleCopy(source, dest):
    try:
        shutil.copy(source, dest)
    except IOError as e:
        print(e)
        exit(1)

def overwriteFile(path, text):
    try:
        fobj = open(path, "w")
        fobj.write(text)
        fobj.close()
    except IOError as e:
        print(e)
        subprocess.call(["lxc-destroy", "-n", tmpName])
        exit(1)


### End of function scope ###

### Execution scope ###

def main():
    if len(sys.argv) < 2:
        print("Specify a program you want to run inside lxc.")
        exit(1)
    program = sys.argv[1]
    # Generate random string for naming the temporarely created container
    tmpName = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(12)])
    returncode = subprocess.call(["lxc-create", "-n", tmpName, "-t", "debian"])
    if returncode != 0:
        print("Unable to create a new linux container. (lxc-create failed!)")
        exit(1)
    # Alter resolv.conf
    overwriteFile(lxc_path + tmpName + "/rootfs/etc/resolv.conf", "nameserver 8.8.4.4")
    # Install lxc into the container
    subprocess.call(["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin chroot /var/lib/lxc/" + tmpName + "/rootfs/ sh -c \'export DEBIAN_FRONTEND=noninteractive; apt-get update; apt-get install -y --force-yes lxc\'"], shell=True)
    # Copy the program into rootfs
    handleCopy(program, lxc_path + tmpName + "/rootfs/")
    # Run the program inside the container
    returncode = subprocess.call(["lxc-execute", "-n", tmpName, "/" + program])
    print("Returncode: " + str(returncode))
    # Finally destroy the container
    subprocess.call(["lxc-destroy", "-n", tmpName])

if __name__ == '__main__':
    main()