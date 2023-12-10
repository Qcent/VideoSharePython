import win32con
import win32gui
import win32ui
import win32api
import numpy as np
import tkinter as tk


def find_window_by_partial_name(partial_name):
    window_handles = []

    def callback(hwnd, param):
        if win32gui.IsWindowVisible(hwnd) and \
                partial_name.lower() in win32gui.GetWindowText(hwnd).lower():
            window_handles.append(hwnd)
        return True

    win32gui.EnumWindows(callback, None)
    return window_handles


def is_window_fullscreen(hwnd, window_width, window_height):
    rect = win32gui.GetWindowRect(hwnd)
    screen_rect = win32api.GetMonitorInfo(win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST))['Monitor']

    screen_width = screen_rect[2] - screen_rect[0]
    screen_height = screen_rect[3] - screen_rect[1]

    #print(f'window: {window_width} x {window_height}') # often 1 pixel larger then expected (from yuzu??)
    #print(f'screen: {screen_width} x {screen_height}')

    return window_width == screen_width and window_height >= screen_height


class WindowCapture:
    # constructor
    def __init__(self, capture_window_name):
        self.window_name = self.search_name = capture_window_name
        self.last_size = 0
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
            self.acquire_window()

    def get_new_window(self, capture_window_name):
        self.window_name = self.search_name = capture_window_name
        self.last_size = 0
        self.acquire_window()

    def is_window_size_changed(self):
        current_size = win32gui.GetWindowRect(self.hwnd)
        if current_size != self.last_size:
            self.acquire_window_size()

    def acquire_window_size(self):
            # get the window size
            window_rect = win32gui.GetWindowRect(self.hwnd)
            self.last_size = window_rect
            self.w = window_rect[2] - window_rect[0]
            self.h = window_rect[3] - window_rect[1]

            fullscreenCheck = is_window_fullscreen(self.hwnd, self.w, self.h)
            # print(f'Fullscreen: {fullscreenCheck}')

            if not fullscreenCheck:
                # account for the window border and titlebar and cut them off
                border_pixels = 8
                titlebar_pixels = 30
                self.w = self.w - (border_pixels * 2)
                self.h = self.h - titlebar_pixels - border_pixels
                self.cropped_x = border_pixels
                self.cropped_y = titlebar_pixels
            else:
                self.cropped_x = 0
                self.cropped_y = 0

            # set the cropped coordinates offset so we can translate screenshot
            # images into actual screen positions
            self.offset_x = window_rect[0] + self.cropped_x
            self.offset_y = window_rect[1] + self.cropped_y

    def acquire_window(self):
        if self.search_name is not None:
            self.hwnd = win32gui.FindWindow(None, self.window_name)
            if not self.hwnd:
                # raise Exception('Window not found: {}'.format(self.window_name))
                self.hwnd = find_window_by_partial_name(self.search_name)
                if not len(self.hwnd):
                    raise Exception('Window not found: {}'.format(self.search_name))
                else:
                    self.hwnd = self.hwnd[0]
                    self.window_name = win32gui.GetWindowText(self.hwnd)

            self.acquire_window_size()

    def get_screenshot(self):
        self.is_window_size_changed()

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
    global selected_window

    def enum_windows_callback(hwnd, window_list):
        if win32gui.IsWindowVisible(hwnd):
            window_name = win32gui.GetWindowText(hwnd)
            if window_name:
                window_list.append((hwnd, window_name))

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

    def refresh_windows():
        window_listbox.delete(2, tk.END)  # Clear existing items
        window_list.clear()  # Clear existing window list
        win32gui.EnumWindows(enum_windows_callback, window_list)

        # Add each window title to the listbox and store its hwnd and process id
        for hwnd, window_title in window_list:
            window_listbox.insert(tk.END, f"{window_title}")
            window_listbox.itemconfig(tk.END, {'bg': 'white', 'fg': 'black'})

    def double_click(event):
        select_window()

    window_list = []
    selected_window = None

    win32gui.EnumWindows(enum_windows_callback, window_list)

    root = tk.Tk()
    root.title("Select a Window to Stream")
    root.geometry("400x360")

    window_listbox = tk.Listbox(root, width=50, height=20)
    window_listbox.pack()

    window_listbox.insert(tk.END, "Web Cam")
    window_listbox.itemconfig(tk.END, {'bg': 'white', 'fg': 'black'})

    window_listbox.insert(tk.END, "Screen Cap")
    window_listbox.itemconfig(tk.END, {'bg': 'white', 'fg': 'black'})

    for hwnd, window_title in window_list:
        window_listbox.insert(tk.END, f"{window_title}")
        window_listbox.itemconfig(tk.END, {'bg': 'white', 'fg': 'black'})

    window_listbox.bind("<Double-Button-1>", double_click)  # Bind double-click event

    refresh_button = tk.Button(root, text=" Refresh ", command=refresh_windows)
    refresh_button.pack(side=tk.LEFT, padx=100)

    select_button = tk.Button(root, text=" Select ", command=select_window)
    select_button.pack(side=tk.LEFT)

    root.mainloop()

    return selected_window

