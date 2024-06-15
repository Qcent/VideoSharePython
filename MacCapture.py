import numpy as np
import pygetwindow as gw
import tkinter as tk

class WindowCapture:
    def __init__(self, capture_window_name):
        if capture_window_name is None:
            self.window = None
            self.w = 1920
            self.h = 1080
            self.cropped_x = 0
            self.cropped_y = 0
            self.offset_x = 0
            self.offset_y = 0
        else:
            self.window = gw.getWindowsWithTitle(capture_window_name)
            if not self.window:
                raise Exception('Window not found: {}'.format(capture_window_name))

            self.window = self.window[0]

            # get the window size
            self.w, self.h = self.window.width, self.window.height

            # account for the window border and titlebar and cut them off
            border_pixels = 8
            titlebar_pixels = 30
            self.w = self.w - (border_pixels * 2)
            self.h = self.h - titlebar_pixels - border_pixels
            self.cropped_x = border_pixels
            self.cropped_y = titlebar_pixels

            # set the cropped coordinates offset, so we can translate screenshot
            # images into actual screen positions
            self.offset_x = self.window.left + self.cropped_x
            self.offset_y = self.window.top + self.cropped_y

    def get_screenshot(self):
        screenshot = np.array(self.window.screenshot())[:, :, :3]
        return screenshot

    def get_screen_position(self, pos):
        return pos[0] + self.offset_x, pos[1] + self.offset_y


def select_a_window():
    # Get a list of all top-level windows
    window_list = gw.getAllTitles()

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

    # Add each window title to the listbox
    for window_title in window_list:
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
