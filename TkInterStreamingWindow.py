import tkinter as tk
from PIL import Image, ImageTk
import struct
from image_converters import webp_bytearray_to_pil, jpeg_bytearray_to_pil
from Args import app_settings
from WinCapture import get_file_path

VIDEO_SIZES = [360, 480, 600, 720, 840, 960, 1200, 1440, 1680, 1920]
WxH_Ratio = 9/16


def clamp_img_size(index):
    # Ensure index stays within the array range
    if index > len(VIDEO_SIZES)-1:
        index = len(VIDEO_SIZES) - 1
    clamped_index = max(0, index)
    return clamped_index


def image_size_up(index):
    return clamp_img_size(index + 1)


def image_size_down(index):
    return clamp_img_size(index - 1)


class ImageSize:

    def __init__(self):
        self.size_index = 5
        self.value = VIDEO_SIZES[self.size_index]

    def set(self, quality):
        self.size_index = clamp_img_size(quality)
        self.value = VIDEO_SIZES[self.size_index]

    def up(self):
        self.size_index = image_size_up(self.size_index)
        self.value = VIDEO_SIZES[self.size_index]
        self.report_size()

    def down(self):
        self.size_index = image_size_down(self.size_index)
        self.value = VIDEO_SIZES[self.size_index]
        self.report_size()

    def report_size(self):
        print(f'Outputting video @ {self.value} x {self.value * WxH_Ratio}|{app_settings.args.quality}% quality')


class TkInterStreamingWindow:
    def __init__(self, image_pil=None, image_path=None, window_name='Video Stream', geometry='800x600', fps_callback=None, callback=None, callback_params=None):
        self.geometry = geometry
        self.root = tk.Tk()
        self.root.title(window_name)
        # Set the window icon
        self.root.iconbitmap(get_file_path('icon_vid.ico'))
        self.root.configure(background='black')
        self.root.geometry(self.geometry)
        # Set the protocol for closing the window
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.minimal = False

        self.callback_func = callback
        self.callback_params = callback_params

        self.fps_callback = fps_callback
        self.window_name = window_name

        # stream variables initialized to None
        self.client_socket = None
        self.payload_size = None
        self.data_holder = {"data": b""}

        # Load the image
        if image_pil:
            self.image = image_pil
        elif image_path:
            self.image = Image.open(get_file_path(image_path))
        else:
            raise Exception("An error occurred during initialization. No image provided.")

        # Store the og size of the image
        self.og_img_width, self.og_img_height = self.image.size

        # Create a label to display the image
        self.image_label = tk.Label(self.root)
        self.image_label.pack(fill=tk.BOTH, expand=True)

        # Bind the resize event to the image label
        self.image_label.bind('<Configure>', self.resize_image)

        # Call the resize_image method initially to set the image size
        self.resize_image(None)
        self.schedule_update()

    def toggle_fullscreen(self, event):
        if self.root.attributes('-fullscreen'):
            self.root.attributes('-fullscreen', False)
            self.root.geometry(self.geometry)  # Set the initial window size
        else:
            self.root.attributes('-fullscreen', True)
            self.root.geometry('')  # Clear the window size

    def toggle_on_top(self, event):
        if self.root.attributes('-topmost'):
            self.root.attributes('-topmost', False)
        else:
            # Set the window to be always on top
            self.root.attributes('-topmost', True)

    def toggle_minimal(self, event):
        self.minimal = not self.minimal
        # toggle the window title bar
        self.root.overrideredirect(self.minimal)

    def original_image_size(self, event):
        self.geometry = f'{self.og_img_width}x{self.og_img_height}+{self.root.winfo_x()}+{self.root.winfo_y()}'
        self.root.geometry(self.geometry)

    def size_window_to_image(self, event):
        # resize to current saved geometry
        self.root.geometry(self.geometry)

    def update_image(self):
        if app_settings.fatal_error:
            return
        self.image = self.get_next_frame()
        if self.image is None:
            # raise Exception('Received image is null')
            print('Received image is null')
            app_settings.fatal_error = True
            self.root.destroy()
        else:
            self.resize_image(None)

    def schedule_update(self):
        if app_settings.fatal_error:
            self.root.destroy()
            return

        self.update_image()
        if self.callback_func:
            self.callback_func(self.callback_params)

        if self.fps_callback:
            fps = self.fps_callback()
            if fps:
                self.root.title(f'{self.window_name}     {fps}')

        if self.image is None:
            # raise Exception('Received image is null')
            print('Received image is null')
            app_settings.fatal_error = True
            self.root.destroy()
            return
        else:
            self.root.after(1, self.schedule_update)  # Call update_image/fps in 1ms (or asap/every loop)?

    def init_video_stream(self, client_socket, payload_size):
        self.client_socket = client_socket
        self.payload_size = payload_size

    def get_next_frame(self):
        if self.client_socket is None or self.payload_size is None:
            return self.image
            # raise Exception("An error occurred. No video stream data provided.")
        while len(self.data_holder["data"]) < self.payload_size:
            packet = self.client_socket.recv(4 * 1024)  # 4K
            if not packet:
                return None
            self.data_holder["data"] += packet

        packed_msg_size = self.data_holder["data"][:self.payload_size]
        self.data_holder["data"] = self.data_holder["data"][self.payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(self.data_holder["data"]) < msg_size:
            self.data_holder["data"] += self.client_socket.recv(4 * 1024)

        frame_data = self.data_holder["data"][:msg_size]
        self.data_holder["data"] = self.data_holder["data"][msg_size:]

        if app_settings.args.codec == 2:
            frame = webp_bytearray_to_pil(frame_data)
        else:
            frame = jpeg_bytearray_to_pil(frame_data)
        ##
        # store the size of the image
        self.og_img_width, self.og_img_height = frame.size
        ##
        return frame

    def resize_image(self, event):
        if self.image is None:
            return
        # Get the window size
        width = self.root.winfo_width()
        height = self.root.winfo_height()

        x_position = self.root.winfo_x()
        y_position = self.root.winfo_y()

        width = 240 if width < 240 else width
        height = 180 if height < 180 else height

        # Calculate the aspect ratio of the image
        aspect_ratio = self.image.width / self.image.height

        # Resize the image while preserving the aspect ratio
        if width / height > aspect_ratio:
            new_width = int(height * aspect_ratio)
            new_height = height
        else:
            new_width = width
            new_height = int(width / aspect_ratio)

        resized_image = self.image.resize((new_width, new_height), Image.ANTIALIAS)

        # Convert the resized image to Tkinter-compatible format
        tk_image = ImageTk.PhotoImage(resized_image)

        # Update the image label
        self.image_label.config(image=tk_image, background='black')
        self.image_label.image = tk_image

        # Update window geometry // but don't do root because its buggy just keep a record
        self.geometry = f'{new_width}x{new_height}+{x_position}+{y_position}'

    def on_close(self):
        print("Window closed.")
        app_settings.KILLED = True
        print("Program exiting.")
        self.root.destroy()

    def exit_app(self, event):
        app_settings.KILLED = True
        print("Program exiting.")
        self.root.destroy()  # or root.destroy() depending on your needs

    def run(self):
        self.root.bind('<Alt-Return>', self.toggle_fullscreen)
        self.root.bind('<Alt-t>', self.toggle_on_top)
        self.root.bind('<Alt-m>', self.toggle_minimal)
        self.root.bind('<Alt-s>', self.size_window_to_image)
        self.root.bind('<Alt-o>', self.original_image_size)

        self.root.bind('<Shift-Escape>', self.exit_app)

        self.root.mainloop()
