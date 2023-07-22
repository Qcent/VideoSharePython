import cv2
import imutils
import socket
import struct
import keyboard
import tkinter as tk

import numpy as np
import pygame
import win32con
import win32gui
import win32ui

from image_converters import cv2_to_pil, pil_to_webp_bytearray, webp_bytearray_to_pil, pil_to_cv2, pil_to_pygame
from TkInterStreamingWindow import TkInterStreamingWindow, VQ
from PyGameImageWindow import PyGameWindow

from KeyboardManager import KeyboardManager

from FPSCounter import FPSCounter
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
VIDEO_QUALITY = VQ()
key_manager = KeyboardManager()


# Toggle fullscreen mode function
def toggle_fullscreen():
    global fullscreen
    fullscreen = not fullscreen
    if fullscreen:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WND_PROP_TOPMOST)
    else:
        cv2.setWindowProperty(window_name, cv2.WINDOW_NORMAL)
    print(f'fullscreen: {fullscreen}')


class WindowCapture:
    # constructor
    def __init__(self, capture_window_name):
        # find the handle for the window we want to capture
        if capture_window_name is None:
            self.hwnd = None
            self.w = 1920
            self.h = 1080
            self.cropped_x = 0
            self.cropped_y = 0
            self.offset_x = 0
            self.offset_y = 0
        else:
            self.hwnd = win32gui.FindWindow(None, capture_window_name)
            if not self.hwnd:
                raise Exception('Window not found: {}'.format(capture_window_name))

            # get the window size
            window_rect = win32gui.GetWindowRect(self.hwnd)
            self.w = window_rect[2] - window_rect[0]
            self.h = window_rect[3] - window_rect[1]

            # account for the window border and titlebar and cut them off
            border_pixels = 8
            titlebar_pixels = 30
            self.w = self.w - (border_pixels * 2)
            self.h = self.h - titlebar_pixels - border_pixels
            self.cropped_x = border_pixels
            self.cropped_y = titlebar_pixels

            # set the cropped coordinates offset so we can translate screenshot
            # images into actual screen positions
            self.offset_x = window_rect[0] + self.cropped_x
            self.offset_y = window_rect[1] + self.cropped_y

    def get_screenshot(self):

        # get the window image data
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

        # convert the raw data into a format opencv can read
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray, dtype='uint8')
        img.shape = (self.h, self.w, 4)

        # free resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # drop the alpha channel, or cv.matchTemplate() will throw an error like:
        #   error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _templ.type()
        #   && _img.dims() <= 2 in function 'cv::matchTemplate'
        img = img[..., :3]

        # make image C_CONTIGUOUS to avoid errors that look like:
        #   File ... in draw_rectangles
        #   TypeError: an integer is required (got type tuple)
        # see the discussion here:
        # https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
        img = np.ascontiguousarray(img)

        return img

    # find the name of the window you're interested in.
    # once you have it, update window_capture()
    # https://stackoverflow.com/questions/55547940/how-to-get-a-list-of-the-name-of-every-open-window
    @staticmethod
    def list_window_names():
        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                print(hex(hwnd), win32gui.GetWindowText(hwnd))

        win32gui.EnumWindows(winEnumHandler, None)

    # translate a pixel position on a screenshot image to a pixel position on the screen.
    # pos = (x, y)
    # WARNING: if you move the window being captured after execution is started, this will
    # return incorrect coordinates, because the window position is only calculated in
    # the __init__ constructor.
    def get_screen_position(self, pos):
        return (pos[0] + self.offset_x, pos[1] + self.offset_y)


def select_a_window():
    # Get a list of all top-level windows
    window_list = []

    def enum_windows_callback(hwnd, window_list):
        if win32gui.IsWindowVisible(hwnd):
            window_name = win32gui.GetWindowText(hwnd)
            if window_name:
                window_list.append((hwnd, window_name))

    win32gui.EnumWindows(enum_windows_callback, window_list)

    # Create a simple GUI to display the window list
    root = tk.Tk()
    root.title("Select a Window to Stream")
    root.geometry("400x360")

    # Create a listbox to display the window titles
    window_listbox = tk.Listbox(root, width=50, height=20)
    window_listbox.pack()

    # Create an Entry for WebCam Cap
    window_listbox.insert(tk.END, f"Web Cam")
    window_listbox.itemconfig(tk.END, {'bg': 'white', 'fg': 'black'})

    # Create an Entry for Full Screen Cap
    window_listbox.insert(tk.END, f"Screen Cap")
    window_listbox.itemconfig(tk.END, {'bg': 'white', 'fg': 'black'})

    # Add each window title to the listbox and store its hwnd and process id
    for hwnd, window_title in window_list:
        window_listbox.insert(tk.END, f"{window_title}")
        window_listbox.itemconfig(tk.END, {'bg': 'white', 'fg': 'black'})

    # Define a function to handle window selection and close the GUI
    def select_window():
        global selected_window
        selection = window_listbox.curselection()
        if selection:
            if selection[0] == 0:
                selected_window = ('webcam', None)
            elif selection[0] == 1:
                selected_window = ('ScreenCap', None)
            else:
                selected_window = window_list[selection[0] - 2]
            root.destroy()

    # Add a button to select the currently highlighted window
    select_button = tk.Button(root, text="Select", command=select_window)
    select_button.pack()

    # Run the GUI and wait for the user to select a window
    root.mainloop()

    # Return the selected hwnd and window title
    return selected_window


def send_frame(conn, img):
    data = pil_to_webp_bytearray(cv2_to_pil(img))
    message = struct.pack("Q", len(data)) + data
    conn.sendall(message)


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

    ## frame_data = webp_bytearray_to_pil(frame_data)
    ## frame = pil_to_cv2(frame_data)
    frame = webp_bytearray_to_pil(frame_data)

    return frame


def send_mode(port):
    # Socket Create
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = '0.0.0.0'
    print('HOST IP:', host_ip)
    socket_address = (host_ip, port)

    # Socket Bind
    server_socket.bind(socket_address)

    # Socket Listen
    server_socket.listen(5)
    print("LISTENING AT:", socket_address)

    # Socket Accept
    while True:
        hwnd = select_a_window()
        # WindowCapture.list_window_names()
        client_socket, addr = server_socket.accept()
        print('GOT CONNECTION FROM:', addr)
        if client_socket:
            if hwnd[0] == 'webcam':
                vid = cv2.VideoCapture(0)
            else:
                wincap = WindowCapture(hwnd[1])

            while True:
                if key_manager.is_pressed_and_released('page_up'):
                    VIDEO_QUALITY.up()
                if key_manager.is_pressed_and_released('page_down'):
                    VIDEO_QUALITY.down()

                if hwnd[0] == 'webcam':
                    img, frame = vid.read()
                else:
                    frame = wincap.get_screenshot()
                    # frame = imutils.resize(frame, width=960)  # half 1080p
                    frame = imutils.resize(frame, width=int(VIDEO_QUALITY.value))

                send_frame(client_socket, frame)


def send_mode2(port, host, hwnd):
    #hwnd = select_a_window()
    # create socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    if hwnd[0] == 'webcam':
        vid = cv2.VideoCapture(0)
    else:
        wincap = WindowCapture(hwnd[1])

    while True:
        if key_manager.is_pressed_and_released('page_up'):
            VIDEO_QUALITY.up()
        if key_manager.is_pressed_and_released('page_down'):
            VIDEO_QUALITY.down()

        if hwnd[0] == 'webcam':
            img, frame = vid.read()
        else:
            frame = wincap.get_screenshot()
            frame = imutils.resize(frame, width=int(VIDEO_QUALITY.value))

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
    host_name = socket.gethostname()
    host_ip = '0.0.0.0'
    socket_address = (host_ip, port)

    # Socket Bind
    server_socket.bind(socket_address)

    # Socket Listen
    server_socket.listen(5)
    print("LISTENING AT:", socket_address)

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
    host_ip = '0.0.0.0'
    print('HOST IP:', host_ip)
    socket_address = (host_ip, port)

    # Socket Bind
    server_socket.bind(socket_address)

    # Socket Listen
    server_socket.listen(5)
    print("LISTENING AT:", socket_address)

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
    if key_manager.is_pressed_and_released('page_up'):
        VIDEO_QUALITY.up()
    if key_manager.is_pressed_and_released('page_down'):
        VIDEO_QUALITY.down()

    client_socket, capture_func = params

    frame = capture_func()
    frame = imutils.resize(frame, width=VIDEO_QUALITY.value)

    send_frame(client_socket, frame)


def send_and_receive_mode(client_socket, hwnd):
    if hwnd[0] == 'webcam':
        capture_source = cv2.VideoCapture(0)
        def cap_frame():
            return capture_source.read()[1]
    else:
        capture_source = WindowCapture(hwnd[1])
        def cap_frame():
            return capture_source.get_screenshot()

    window = TkInterStreamingWindow(window_name=window_name, image_path='bg.jpg', fps_callback=do_fps_counting,
                                    callback=send_receive_tkinter_loop,
                                    callback_params=(client_socket, cap_frame))

    # Pass network info to tkinter window object
    window.init_video_stream(client_socket, struct.calcsize("Q"))

    # run the tkinter loop
    window.run()

