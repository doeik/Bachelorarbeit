import json
import os
import socket
import sys

SERVER_ADDRESS = "./uds_lxcdaemon"


def main():
    arglist = [os.path.abspath(sys.argv[1])]
    arglist.extend(sys.argv[2:])
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
    	client_socket.connect(SERVER_ADDRESS)
    except Exception as e:
    	print(e)
    else:
    	try:
            fd = client_socket.makefile("w")
            fd.write(json.dumps(arglist))
            fd.write("\n")
            fd.close()
    	except Exception as e:
    		print(e)
    	else:
            reply = client_socket.recv(128).decode()
            print("lxc_daemon_client: " + reply)



if __name__ == "__main__":
    main()
