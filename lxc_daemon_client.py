import socket
import sys

SERVER_ADDRESS = "./uds_lxcdaemon"


def main():
    msg = "#" + sys.argv[1]
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
    	finally:
    		toServer_socket.close()


if __name__ == "__main__":
    main()
