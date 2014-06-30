import base64
import io
import json
import socket
import sys

UDS_SOCKET = "./uds_lxcdaemon"


def main():
    dict_request = {"keep-alive": False, "action": "run_prog", "timeout": 2}
    fd_program = io.open(sys.argv[1], "rb")
    program = base64.b64encode(fd_program.read())
    fd_program.close()
    dict_request["b64_data"] = str(program, encoding="utf8")
    arglist = sys.argv[1:]
    dict_request["params"] = arglist
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client_socket.connect(UDS_SOCKET)
    except Exception as e:
        print(e)
    else:
        fd = client_socket.makefile("rw")
        fd.write(json.dumps(dict_request))
        fd.write("\n")
        fd.flush()
        reply = client_socket.recv(128).decode()
        fd.close()
        print("lxc_daemon_client: " + reply.rstrip("\n"))


if __name__ == "__main__":
    main()
