import io
import lxc
import optparse
import os
import subprocess

CONFIG_TEMPLATE = "/usr/local/lib/lxc_daemon/config_template"
NAMESERVER = "8.8.4.4"


def makeConfigFromTemplate(cont):
    container_path = os.path.dirname(cont.config_file_name)
    with io.open(CONFIG_TEMPLATE, "r") as config:
        content = config.readlines()
    for i, line in enumerate(content):
        line = line.replace("{container}", container_path)
        line = line.replace("{name}", cont.name)
        content[i] = line
    with io.open(cont.config_file_name, "w") as newconf:
        for line in content:
            newconf.write(line)


def packageInstall(cont, pkg_list):
    cont_rootfs = cont.get_config_item("lxc.rootfs")
    with io.open(os.path.join(cont_rootfs, "etc/resolv.conf"), "w") as dnsfile:
        dnsfile.write("nameserver " + NAMESERVER)
    for package in pkg_list:
        ret = subprocess.call("PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin chroot " + cont_rootfs
                              + " sh -c 'export DEBIAN_FRONTEND=noninteractive; apt-get update; apt-get install -y --force-yes " + package + "'", shell=True)
        if ret != 0:
            print("tc_setup: failed to install package " + package)


def containerSetup(name, args):
    cont = lxc.Container(name)
    cont.create("debian")
    if not cont.defined:
        return 1
    makeConfigFromTemplate(cont)
    if len(args) < 1:
        print("no packages to be installed specified")
    else:
        packageInstall(cont, args)
    return 0


def main():
    if os.geteuid() != 0:
        print("must be run as root")
        exit(1)
    parser = optparse.OptionParser()
    parser.add_option("-n", "--name", action="store",
                      dest="name", help="avoid interactive mode by specifying a container name with this option")
    (options, args) = parser.parse_args()
    if options.name != None:
        ret = containerSetup(options.name, args)
    else:
        name = input("please enter the name of the template container: ")
        ret = containerSetup(name, args)
    exit(ret)


if __name__ == "__main__":
    main()
