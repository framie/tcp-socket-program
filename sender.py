import socket                   # for sockets
import hashlib                  # for generating the 256-bit (32-byte) checksum hash
import pickle                   # for converting Packet class to bytes
import argparse                 # for reading command line input
from packet import Packet       # for Packet class
from select import select       # for select() function
from copy import deepcopy       # for deepcopy() function
from sys import exit            # for exit()
from pathlib import Path        # for path()
from channel import get_args, check_port


def exit_sender(s_in, s_out, file="", fileOpen=False, packets_sent=0):
    """ Closes file and all sockets, then exits the program.
    """      
    s_in.close()
    s_out.close()
    if fileOpen:
        file.close()
    print("Total packets sent:", packets_sent)
    exit()  

def main():
    args = get_args(["s_in", "s_out", "cs_in"], True)
    s_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_out = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s_in.bind(('127.0.0.1', args.s_in))  

    seq_next = 0
    exit_flag = False
    channel_conn = 0
    packets_sent = 0
    read_list = [s_in]
    
    my_file = Path(args.filename)
    if not my_file.is_file():
        print("File doesn't exist - exiting...")
        exit_sender(s_in, s_out)
    f = open(args.filename, 'r')
    
    while 1:
        exit_loop = False
        fileData = f.read(512)
        if len(fileData) == 0:
            newPacket = Packet(seqno = seq_next)
            exit_flag = True
        else:
            newPacket = Packet(seqno = seq_next, dataLen = len(fileData), data = fileData)
        
        packetBuffer = deepcopy(newPacket)
    
        if channel_conn == 0:
            s_out.connect(('127.0.0.1', args.s_out))
            s_in.listen(1)
        
        while not exit_loop:
            s_out.sendall(pickle.dumps(packetBuffer))
            packets_sent += 1
            if select(read_list, [], [], 1)[0]:
                if channel_conn == 0:
                    channel_conn = s_in.accept()
                    read_list.append(channel_conn[0])
                if select(read_list, [], [], 1)[0]:
                    try:
                        data = pickle.loads(channel_conn[0].recv(1024))
                    except EOFError:
                        exit_sender(s_in, s_out, f, channel_conn, packets_sent)
                    if data.magicno == 0x497E and data.type == "acknowledgementPacket":
                        if data.checksum == hashlib.md5((data.data).encode()).hexdigest():    # check for bit-error
                            data.dataLen = len(data.data)     # correct bit-error
                            if data.dataLen == 0 and data.seqno == seq_next:
                                seq_next = 1 - seq_next
                                if exit_flag:
                                    exit_sender(s_in, s_out, f, channel_conn, packets_sent)
                                exit_loop = True


if __name__ == "__main__":
    main()