import socket                   # for sockets
import pickle                   # for converting Packet class to bytes
import argparse                 # for reading command line input
import random                   # for generating random numbers
from select import select       # for select() function
from sys import exit            # for exit()


def exit_channel(cs_in, cs_out, cr_in, cr_out):
    """ Closes all sockets, then exits the program.
    """
    cs_in.close()
    cs_out.close()
    cr_in.close()
    cr_out.close()   
    exit()      


def send_packet(dest, received, p, sockets, packetSent, cr_out=0):
    """ Using input received data, checks if the packet is valid, randomly causes a
        simulated packet loss and bit-error, then sends the packet to the destination socket.
    """
    try:
        data = pickle.loads(received[0].recv(1024))
    except EOFError:
        exit_channel(sockets[0], sockets[1], sockets[2], sockets[3])
    if data.magicno == 0x497E:
        if random.random() > p:     # checks for packet loss
            if packetSent == 0:
                sockets[3].connect(('127.0.0.1', cr_out))
            if random.random() < 0.1:   # bit error
                data.dataLen += random.randint(1, 10)
            dest.sendall(pickle.dumps(data))   


def check_port(num):
    """ Checks the input string to see if it a valid port number. If not,
        raises an ArgumentTypeError with message.
    """
    port = int(num)
    if port < 1024 or port > 64000:
        raise argparse.ArgumentTypeError("Number must be between 1,024 and 64,000.")
    return port


def check_p(num):
    """ Checks the input string to see if it a valid P value. If not,
        raises an ArgumentTypeError with message.
    """    
    p = float(num)
    if p < 0 or p >= 1:
        raise argparse.ArgumentTypeError("Number must be within 0 <= P < 1")
    return p        


def get_args(socket_list, file_needed=False, p_needed=False):
    """ Retrieves information from command line, based on what arguments are included
        when called.
    """    
    parser = argparse.ArgumentParser()
    for i in range(len(socket_list)):
        parser.add_argument(socket_list[i], type=check_port, help="Port number for " + socket_list[i])
    if p_needed:
        parser.add_argument("P", type=check_p, help="Packet loss rate")
    if file_needed:
        parser.add_argument("filename", type=str, help="Filename for program use")
    return parser.parse_args()
    
    
def main():
    args = get_args(["cs_in", "cs_out", "cr_in", "cr_out", "s_in", "r_in"], False, True)
    cs_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cs_out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cr_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cr_out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_list = [cs_in, cs_out, cr_in, cr_out]
    cs_in.bind(('127.0.0.1', args.cs_in))
    cr_in.bind(('127.0.0.1', args.cr_in)) 
    cs_in.listen(1)
    cr_in.listen(1)
    
    p_val = args.P                  # packet loss rate
    sender_conn = 0
    receiver_conn = 0
    read_list = [cs_in, cr_in]

    while 1:
        readable, writable, special = select(read_list, [], [])
        if cs_in in readable or (sender_conn != 0 and sender_conn[0] in readable):
            if sender_conn == 0:
                sender_conn = cs_in.accept()
                read_list.append(sender_conn[0])
            send_packet(cr_out, sender_conn, p_val, socket_list, receiver_conn, 5003)
        if cr_in in readable or (receiver_conn != 0 and receiver_conn[0] in readable):
            if receiver_conn == 0:
                cs_out.connect(('127.0.0.1', args.cs_out))
                receiver_conn = cr_in.accept()
                read_list.append(receiver_conn[0])
            send_packet(cs_out, receiver_conn, p_val, socket_list, receiver_conn)


if __name__ == "__main__":
    main()