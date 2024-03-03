from Args import app_settings
from video_frames import send_mode, send_mode2, receive_mode, receive_mode2, send_and_receive_mode, \
    start_as_client, start_as_server, window_supplied_or_select
import traceback
import time


def get_arg_settings(args):
    # set port
    if args.port:
        PORT = int(args.port)
    else:
        PORT = 5001
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

    if not hasattr(args, 'window'):
        args.window = ''

    return PORT, HOST, OPS_MODE


PORT, HOST, OPS_MODE = get_arg_settings(app_settings.args)
restart_count =0

while not app_settings.KILLED:
    try:
        if OPS_MODE > 3:
            ##hwnd = select_a_window()
            hwnd = window_supplied_or_select()

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

    except Exception as e:
        restart_count += 1
        if restart_count > 3:
            print(f"Fatal Error: {e}")
            traceback.print_exc()

            time.sleep(0.1)
            input("   << Multiple Crashes Detected >>\n\tPress Enter to Restart...")
            restart_count = 0
        else:
            print(f"Fatal Error: {e}")
            traceback.print_exc()

            if 'Window not found:'.lower() in f"{e}".lower():
                app_settings.args.window = None

            time.sleep(0.02)
            print("Restarting Program")

