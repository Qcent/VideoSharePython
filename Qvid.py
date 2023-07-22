import argparse
from video_frames import send_mode, send_mode2, receive_mode, receive_mode2, send_and_receive_mode, start_as_client, start_as_server, select_a_window


def get_parsed_args():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Send video data to a computer over tcp/ip')

    # Add arguments to the parser
    parser.add_argument('-n', '--host', type=str, help='IP address of host/server')
    parser.add_argument('-p', '--port', type=str, help='Port to run on')
    parser.add_argument('-m', '--mode', type=int, help='Operational Mode: 1: Server/TX, 2: Client/RX, 3: Server/RX, 4: Client/TX')

    # Parse and return the arguments
    return parser.parse_args()


def get_arg_settings(args):
    # set port
    if args.port:
        PORT = int(args.port)
    else:
        PORT = 5000
    # set fps

    # set host address
    if args.host:
        HOST = args.host
    else:
        HOST = '127.0.0.1'

    # OPS_MODE 1:Sender 2:Receiver
    if args.mode:
        OPS_MODE = args.mode
    elif args.host:
        OPS_MODE = 2
    else:
        OPS_MODE = 1

    return PORT, HOST, OPS_MODE


args = get_parsed_args()
PORT, HOST, OPS_MODE = get_arg_settings(args)

if OPS_MODE > 3:
    hwnd = select_a_window()

if OPS_MODE == 6:                           # Connects then Sends and Receives data
    #hwnd = select_a_window()
    socket = start_as_client(PORT, HOST)
    send_and_receive_mode(socket, hwnd)
if OPS_MODE == 5:                           # Listens for Connection then Sends and Receives data
    #hwnd = select_a_window()
    socket = start_as_server(PORT)
    send_and_receive_mode(socket, hwnd)
if OPS_MODE == 4:
    send_mode2(PORT, HOST, hwnd)    # Connects and Sends data
if OPS_MODE == 3:
    receive_mode2(PORT)       # Listens for Connection and Receives data
if OPS_MODE == 1:
    send_mode(PORT)           # Listens for Connection and Sends data
else:
    receive_mode(PORT, HOST)  # Connects and Receives data
