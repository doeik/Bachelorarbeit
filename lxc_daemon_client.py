import os
import socket
import sys

SERVER_ADDRESS = "./uds_lxcdaemon"


def main():
    msg = "#" + os.path.abspath(sys.argv[1])
    if sys.argv[1] == "stop":
        msg = "!"
    toServer_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
    	toServer_socket.connect(SERVER_ADDRESS)
    except Exception as e:
    	print(e)
    else:
    	try:
    		toServer_socket.sendall(msg.encode())
    	except Exception as e:
    		print(e)
    	else:
            reply = toServer_socket.recv(16).decode()
            print("lxc_daemon_client: " + reply)



if __name__ == "__main__":
    main()
