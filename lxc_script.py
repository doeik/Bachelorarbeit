### Variables that may be changed ###
lxc_path = "/var/lib/lxc/"

### Imports ###

from subprocess import call
from subprocess import check_output
from sys import exit
from sys import argv
from shutil import copy
from os import remove

### Function scope ###

def callLxcCreate():
	call(["brctl", "addbr", "br-lxc"])
	call(["lxc-create", "-n", "arch", "-t", "archlinux"])

def getContainers():
	return check_output("lxc-ls").decode(encoding='UTF-8')

def getContainerState(container):
	splitstr = check_output(["lxc-info", "-n", container]).decode(encoding='UTF-8').split()
	return splitstr[3]

### End of function scope ###

### Execution scope ###

if len(argv) < 2:
	print("Specify a program you want to run inside lxc.")
	exit(1)
program = argv[1]
container_list = getContainers().split()
if len(container_list) < 1:
	print("Container list appears to be empty. This could be due to running this script without root privileges.")
	exit(1)
# Search container list for available containers and if found run the specified program inside that particular one.
# TODO: error handling
container_found = False
for cont in container_list:
	if getContainerState(cont) == "STOPPED":
		container_found = True
		copy(program, lxc_path + cont + "/rootfs/")
		call(["lxc-execute", "-n", cont, program])
		remove(lxc_path + cont + "/rootfs/" + program)
		break
if container_found == False:
	print("Unable to find an available container. Use \"lxc-ls -f\" to check the container states.")