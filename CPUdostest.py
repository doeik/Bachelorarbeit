import lxc
import threading


def timerEvent(cont):
    cont.stop()


def doCPUdos(cont, command):
    t = threading.Timer(2, timerEvent, (cont, ))
    t.start()
    cont.attach_wait(
        lxc.attach_run_command, command, attach_flags=lxc.LXC_ATTACH_DEFAULT)


def main():
    cont_1 = lxc.Container("demo")
    cont_2 = lxc.Container("demo_lowprio")
    cont_1.start()
    cont_2.start()
    thread1 = threading.Thread(None, doCPUdos, args=(cont_1, "/cpudos1"))
    thread2 = threading.Thread(None, doCPUdos, args=(cont_2, "/cpudos2"))
    thread1.start()
    thread2.start()

if __name__ == "__main__":
    main()
