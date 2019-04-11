import socket                   # for sockets
import hashlib                  # for generating the 256-bit (32-byte) checksum hash
import pickle                   # for converting Packet class to bytes
import argparse                 # for reading command line input
from packet import Packet       # for Packet class
from sys import exit            # for exit()
from pathlib import Path        # for path()
from channel import get_args, check_port


def exit_receiver(r_in, r_out, file="", fileOpen=False):
    """ Closes file and all sockets, then exits the program.
    """    
    r_out.close()
    r_in.close()
    if fileOpen:
        file.close()
    exit()

def main():
    args = get_args(["r_in", "r_out", "cr_in"], True)
    r_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    r_out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    r_in.bind(('127.0.0.1', args.r_in))

    expected = 0
    conn = 0

    my_file = Path(args.filename)
    if my_file.is_file():
        print("File already exists - exiting...")
        exit_receiver(r_in, r_out)
    f = open(args.filename, 'w')
    
    r_in.listen(1)
    channel_conn = r_in.accept()[0]
    r_out.connect(('127.0.0.1', args.r_out))
    
    while 1:
        data = pickle.loads(channel_conn.recv(1024))
        if data.magicno == 0x497E:
            if data.type == "dataPacket":
                if data.checksum == hashlib.md5((data.data).encode()).hexdigest():     # check for bit-error
                    data.dataLen = len(data.data)                                      # correct bit-error
                    ack = Packet("acknowledgementPacket", data.seqno, 0)
                    r_out.sendall(pickle.dumps(ack))                    
                    if data.seqno == expected:
                        expected = 1 - expected
                        if data.dataLen > 0:
                            f.write(data.data)
                        else:
                            exit_receiver(r_in, r_out, f, channel_conn)


if __name__ == "__main__":
    main()  