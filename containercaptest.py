import lxc
import shutil


def main():
    tmpName = "test2"
    container = lxc.Container(tmpName)
    container.create("debian")
    ''' shared library needed by captest. make sure to have the libcap2 package installed '''
    shutil.copy("/usr/lib/libcap.so.2", "/var/lib/lxc/test2/rootfs/usr/lib/")
    shutil.copy("./captest", "/var/lib/lxc/test2/rootfs/")
    container.start()
    container.attach_wait(
        lxc.attach_run_command, "/captest", attach_flags=lxc.LXC_ATTACH_DEFAULT, extra_env_vars=("PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin", ))
    container.stop()
    container.destroy()

if __name__ == "__main__":
    main()
