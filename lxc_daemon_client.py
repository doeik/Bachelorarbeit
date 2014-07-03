import base64
import io
import json
import socket
import sys
import traceback

UDS_SOCKET = "./uds_lxcdaemon"


def main():
    dict_request = {"keep-alive": False, "action": "run_prog", "timeout": 10}
    fd_program = io.open(sys.argv[1], "rb")
    program = base64.b64encode(fd_program.read())
    fd_program.close()
    dict_request["b64_data"] = str(program, encoding="utf8")
    arglist = sys.argv[1:]
    dict_request["params"] = arglist
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client_socket.connect(UDS_SOCKET)
    except Exception:
        traceback.print_exc()
    else:
        fd = client_socket.makefile("rw")
        fd.write(json.dumps(dict_request) + "\n")
        fd.flush()
        recv_data = fd.readline()
        fd.close()
        dict_response = json.loads(recv_data)
        print("lxc_daemon_client:")
        if dict_response["success"] == True:
            print("returncode: " + str(dict_response["returncode"]))
            print("timeout: " + str(dict_response["timeout"]))
        else:
            print(dict_response["info"])


if __name__ == "__main__":
    main()
