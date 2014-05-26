### Variables that may be changed ###

lxc_path = "/var/lib/lxc/"
timeout = 0
container_amount = 5			# Set to anything higher than 0.

### Imports ###

from subprocess import call
from subprocess import check_output
from sys import exit
from sys import argv
from shutil import copy
from os import remove

### Globals ###

container_count = 0

### Function scope ###

def getContainers():
	return check_output("lxc-ls").decode(encoding='UTF-8')

def getContainerState(container):
	splitstr = check_output(["lxc-info", "-n", container]).decode(encoding='UTF-8').split()
	return splitstr[3]

def initContainers():
	container_list = getContainers().split()
	container_count = len(container_list)
	if container_count < 1:
		print("WARNING: Container list appears to be empty. Either you are running this script for the first time or you do not have enough privileges.")
	while container_count < container_amount:
		container_count += 1
		returncode = call(["lxc-create", "-n", "test" + str(container_count), "-t", "debian"])
		if returncode != 0:
			print("Unable to create a new linux container. (lxc-create failed!)")
			exit(1)

def rebuildContainer(cont):
	print("Destroying " + cont + "...")
	call(["lxc-destroy", "-n", cont])
	print("Rebuilding" + cont + "...")
	call(["lxc-create", "-n", cont, "-t", "debian"])

def handleCopy(source, dest):
	try:
		copy(source, dest)
	except IOError as e:
		print(e)
		exit(1)

def handleRemove(path):
	try:
		remove(path)
	except IOError as e:
		print(e)
		exit(1)

### End of function scope ###

### Execution scope ###

initContainers()
if len(argv) < 2:
	print("Specify a program you want to run inside lxc.")
	exit(0)
program = argv[1]
container_list = getContainers().split()
# Search container list for available containers and if found run the specified program inside that particular one.
# TODO: - timeout
container_found = False
for cont in container_list:
	if getContainerState(cont) == "STOPPED":
		container_found = True
		handleCopy(program, lxc_path + cont + "/rootfs/")
		print("Starting " + cont + "...")
		call(["lxc-start", "-n", cont, "-d"])
		print("Executing " + program + "...")
		returncode = call(["lxc-attach", "-n", cont, "/" + program])
		print("Returncode: " + str(returncode))
		print("Stopping " + cont + "...")
		call(["lxc-stop", "-n", cont, "-t", "5"])
		#handleRemove(lxc_path + cont + "/rootfs/" + program)
		rebuildContainer(cont)
		break
if container_found == False:
	print("Unable to find an available container. Use \"lxc-ls -f\" to check the container states.")