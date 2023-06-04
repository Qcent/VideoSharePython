import tkinter as tk
from PIL import Image, ImageTk
import struct
from image_converters import webp_bytearray_to_pil


class TkInterStreamingWindow:
    def __init__(self, image_pil=None, image_path=None, window_name='Video Stream', fps_callback=None):
        self.root = tk.Tk()
        self.root.title(window_name)
        self.root.configure(background='black')
        self.root.geometry('800x600')

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
            self.image = Image.open(image_path)
        else:
            raise Exception("An error occurred during initialization. No image provided.")

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
            self.root.geometry('960x540')  # Set the initial window size
        else:
            self.root.attributes('-fullscreen', True)
            self.root.geometry('')  # Clear the window size

    def update_image(self):
        self.image = self.get_next_frame()
        self.resize_image(None)

    def schedule_update(self):
        self.update_image()
        if self.fps_callback:
            fps = self.fps_callback()
            if fps:
                # print(fps)
                self.root.title(f'{self.window_name}     {fps}')
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

        frame = webp_bytearray_to_pil(frame_data)

        return frame

    def resize_image(self, event):
        # Get the window size
        width = self.root.winfo_width()
        height = self.root.winfo_height()

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
        # self.root.geometry(f'{new_width}x{new_height}')

    def exit_app(self, event):
        self.root.quit()  # or root.destroy() depending on your needs

    def run(self):
        # start a delayed update callback
        # self.schedule_update()

        self.root.bind('<Alt-Return>', self.toggle_fullscreen)
        self.root.bind('<Shift-Escape>', self.exit_app)
        self.root.mainloop()
