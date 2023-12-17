import cv2
import imutils
import socket
import struct
import urllib.request
import win32gui
import sys
import time
from KeyboardManager import KeyboardManager
from image_converters import cv2_to_pil, pil_to_webp_bytearray, webp_bytearray_to_pil, pil_to_jpeg_bytearray, \
    jpeg_bytearray_to_pil  # , pil_to_cv2, pil_to_pygame
from TkInterStreamingWindow import TkInterStreamingWindow, ImageSize
# from PyGameImageWindow import PyGameWindow
from FPSCounter import FPSCounter
from WinCapture import find_window_by_partial_name
from Args import app_settings

# do some arg/setting manipulation to enforce default settings
if app_settings.args.quality is None:
    app_settings.args.quality = 70
if app_settings.args.codec is None or \
        app_settings.args.codec > 2:
    app_settings.args.codec = 1

if sys.platform.startswith('win'):
    # Code block for Windows
    from WinCapture import WindowCapture, select_a_window

    print("Running on Windows")

elif sys.platform.startswith('darwin'):
    # Code block for macOS
    from MacCapture import WindowCapture, select_a_window

    print("Running on macOS")

else:
    # Code block for other platforms (Linux, Unix, etc.)
    print("Platform Capture Unsupported")

fps_counter = FPSCounter()


def do_fps_counting():
    fps_counter.increment_frame_count()
    if fps_counter.frame_count > 30:
        fps = fps_counter.get_fps()
        fps_counter.reset()
        return f"FPS: {fps:.2f}"


# Name of video window
window_name = 'Video Jutsu'
# Flag to track the window mode
fullscreen = False
# Global Video Quality
VIDEO_SIZE = ImageSize()
key_manager = KeyboardManager()


def window_supplied_or_select():
    if hasattr(app_settings.args, 'window') and app_settings.args.window:
        window_list = find_window_by_partial_name(app_settings.args.window)
        if len(window_list):
            window_hndl = window_list[0]
            window_name = win32gui.GetWindowText(window_hndl)
            print(f"Found Window: '{window_name}'")
            hwnd = (window_hndl, app_settings.args.window)
        else:
            raise Exception('Window not found: {}'.format(app_settings.args.window))
            # print(f"Window '{app_settings.args.window}' not found.")
    else:
        hwnd = select_a_window()

    return hwnd


# Toggle fullscreen mode function
def toggle_fullscreen():
    global fullscreen
    fullscreen = not fullscreen
    if fullscreen:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WND_PROP_TOPMOST)
    else:
        cv2.setWindowProperty(window_name, cv2.WINDOW_NORMAL)
    print(f'fullscreen: {fullscreen}')


def send_frame(conn, img):
    if app_settings.args.codec == 2:
        data = pil_to_webp_bytearray(cv2_to_pil(img), app_settings.args.quality)
    else:
        data = pil_to_jpeg_bytearray(cv2_to_pil(img), app_settings.args.quality)

    message = struct.pack("Q", len(data)) + data
    conn.sendall(message)


# receive frame is not used, TkInterStreamingWindow.get_next_frame provides this functionality
'''
def receive_frame(client_socket, payload_size, data_holder):
    while len(data_holder["data"]) < payload_size:
        packet = client_socket.recv(4 * 1024)  # 4K
        if not packet:
            return None
        data_holder["data"] += packet

    packed_msg_size = data_holder["data"][:payload_size]
    data_holder["data"] = data_holder["data"][payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    while len(data_holder["data"]) < msg_size:
        data_holder["data"] += client_socket.recv(4 * 1024)

    frame_data = data_holder["data"][:msg_size]
    data_holder["data"] = data_holder["data"][msg_size:]

    ## frame = pil_to_cv2(frame_data)

    if app_settings.args.codec == 2:
        frame = webp_bytearray_to_pil(frame_data)
    else:
        frame = jpeg_bytearray_to_pil(frame_data)

    return frame
'''


def find_and_print_IP_info(port):
    # Identify and output internal and external ip addresses
    hostname = socket.gethostname()
    lan_ip = socket.gethostbyname(hostname)
    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    print(f'Waiting for Connection on port: {port}\n\t\t LAN: {lan_ip}\n\t\t WAN: {external_ip}')


def set_image_quality(quality):
    if quality > 0 and quality < 101:
        app_settings.args.quality = quality
    # print(f'Image Quality : {app_settings.args.quality}')
    VIDEO_SIZE.report_size()


def check_key_presses(wincap):
    # Alt must be pressed for hotkeys to work
    if key_manager.is_pressed('alt'):
        if key_manager.is_pressed_and_released('page_up'):
            VIDEO_SIZE.up()
        if key_manager.is_pressed_and_released('page_down'):
            VIDEO_SIZE.down()

        if key_manager.is_pressed_and_released('+'):
            set_image_quality(app_settings.args.quality + 1)
        if key_manager.is_pressed_and_released('-'):
            set_image_quality(app_settings.args.quality - 1)

        # sleep to hopefully fix a lag
        if key_manager.is_pressed_and_released('home'):
            print("sleeping ...")
            time.sleep(0.2)
            print("awake")

        if key_manager.is_pressed_and_released('S'):
            if wincap:
                wincap.get_new_window(select_a_window()[1])


def send_mode(port):
    hwnd = window_supplied_or_select()

    # Socket Create
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_ip = '0.0.0.0'

    ##print('HOST IP:', listen_ip)
    socket_address = (listen_ip, port)

    # Socket Bind
    server_socket.bind(socket_address)

    # Socket Listen
    server_socket.listen(5)
    ##print("LISTENING AT:", socket_address)

    # Display IP addresses
    find_and_print_IP_info(port)

    # Socket Accept
    client_socket, addr = server_socket.accept()
    print('GOT CONNECTION FROM:', addr)

    if app_settings.args.size is not None:
        VIDEO_SIZE.set(app_settings.args.size)

    VIDEO_SIZE.report_size()

    frame_limit = 1 / 50  # in practice equates to ~25fps (on my machine ofcourse)
    # calculating a frame time always results in much slower then expected framerate; hard code for now

    if client_socket:
        if hwnd[0] == 'webcam':
            vid = cv2.VideoCapture(0)
        else:
            wincap = WindowCapture(hwnd[1])

        while True:
            check_key_presses(wincap)

            if hwnd[0] == 'webcam':
                img, frame = vid.read()
            else:
                frame = wincap.get_screenshot()
                frame = imutils.resize(frame, width=int(VIDEO_SIZE.value))

            send_frame(client_socket, frame)

            if app_settings.args.codec == 1:
                time.sleep(frame_limit)


def send_mode2(port, host, hwnd):
    # hwnd = select_a_window()
    # create socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    if hwnd[0] == 'webcam':
        vid = cv2.VideoCapture(0)
    else:
        wincap = WindowCapture(hwnd[1])

    if app_settings.args.size is not None:
        VIDEO_SIZE.set(app_settings.args.size)

    VIDEO_SIZE.report_size()

    while True:
        check_key_presses(wincap)

        if hwnd[0] == 'webcam':
            img, frame = vid.read()
        else:
            frame = wincap.get_screenshot()
            frame = imutils.resize(frame, width=int(VIDEO_SIZE.value))

        send_frame(client_socket, frame)

    client_socket.close()


def receive_mode(port, host):
    ### # Create a tkinter window
    window = TkInterStreamingWindow(window_name=window_name, image_path='bg.jpg', fps_callback=do_fps_counting)

    ## # Create pygame window
    ## bg_image = pygame.image.load('bg.jpg')
    ## window = PyGameWindow(bg_image, window_name='Jesus take the frame rate')

    # # Create a named window
    # cv2.namedWindow(window_name)

    # # Register Alt+Enter as the toggle key combination
    # keyboard.add_hotkey('alt + enter', toggle_fullscreen)

    # Create socket and connect to host
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Set up data & payload size values
    payload_size = struct.calcsize("Q")
    data_holder = {"data": b""}

    ### # Pass network info to tkinter window object
    window.init_video_stream(client_socket, payload_size)

    ### # run the tkinter loop
    window.run()

    ## running = window.start()
    '''
    # Below is the cv2 and pygame loop
    while True:
        fps = do_fps_counting()
        if fps:
            ## window.append_window_name(fps)
            print(fps)
        frame = receive_frame(client_socket, payload_size, data_holder)
        if fullscreen:
            frame = imutils.resize(frame, width=1920)
        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) == ord('q'):
            break
    
        ## window.update_image(pil_to_pygame(frame))
        ## running = window.run()
    '''
    client_socket.close()


def receive_mode2(port):
    # Socket Create
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_ip = '0.0.0.0'
    socket_address = (listen_ip, port)

    # Socket Bind
    server_socket.bind(socket_address)

    # Socket Listen
    server_socket.listen(5)
    ## print("LISTENING AT:", socket_address)

    # Display IP addresses
    find_and_print_IP_info(port)

    # Socket Accept
    client_socket, addr = server_socket.accept()
    print('GOT CONNECTION FROM:', addr)

    # Create a named window
    ### cv2.namedWindow(window_name)

    # Register Alt+Enter as the toggle key combination
    ### keyboard.add_hotkey('alt + enter', toggle_fullscreen)

    # Create a tkinter window
    window = TkInterStreamingWindow(window_name=window_name, image_path='bg.jpg', fps_callback=do_fps_counting)

    # Set up network data
    data_holder = {"data": b""}
    payload_size = struct.calcsize("Q")

    # Pass network info to tkinter window object
    window.init_video_stream(client_socket, payload_size)

    # run the tkinter loop
    window.run()

    '''
    while True:
        frame = receive_frame(client_socket, payload_size, data_holder)
        if fullscreen:
            frame = imutils.resize(frame, width=1920)
        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) == ord('q'):
            break
    '''

    client_socket.close()


def start_as_server(port):
    # Socket Create
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_ip = '0.0.0.0'
    socket_address = (listen_ip, port)

    # Socket Bind
    server_socket.bind(socket_address)

    # Socket Listen
    server_socket.listen(5)

    # Display IP addresses
    find_and_print_IP_info(port)

    # Socket Accept
    client_socket, addr = server_socket.accept()
    print('GOT CONNECTION FROM:', addr)

    return client_socket


def start_as_client(port, host):
    # Create socket and connect to host
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    return client_socket


def send_receive_tkinter_loop(params):
    client_socket, capture_func, wincap = params

    check_key_presses(wincap)

    frame = capture_func()
    frame = imutils.resize(frame, width=VIDEO_SIZE.value)

    send_frame(client_socket, frame)


def send_and_receive_mode(client_socket, hwnd):
    if hwnd[0] == 'webcam':
        capture_source = cv2.VideoCapture(0)

        def cap_frame():
            return capture_source.read()[1]

        reacquire = False
    else:
        capture_source = WindowCapture(hwnd[1])

        def cap_frame():
            return capture_source.get_screenshot()

        reacquire = capture_source

    if app_settings.args.size is not None:
        VIDEO_SIZE.set(app_settings.args.size)

    VIDEO_SIZE.report_size()

    window = TkInterStreamingWindow(window_name=window_name, image_path='bg.jpg', fps_callback=do_fps_counting,
                                    callback=send_receive_tkinter_loop,
                                    callback_params=(client_socket, cap_frame, reacquire))

    # Pass network info to tkinter window object
    window.init_video_stream(client_socket, struct.calcsize("Q"))

    # run the tkinter loop
    window.run()
