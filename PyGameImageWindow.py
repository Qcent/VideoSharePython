import pygame


class PyGameWindow:
    def __init__(self, initial_surface, window_name='Video Stream'):
        pygame.init()
        self.running = False
        self.surface = None
        self.window = None
        self.window_name = window_name

        # Create a resizable Pygame window
        self.window_width, self.window_height = initial_surface.get_size()
        self.window = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        pygame.display.set_caption(self.window_name)
        self.set_image(initial_surface)

    def set_image(self, surface):
        self.surface = surface
        # self.window = pygame.display.set_mode(self.surface.get_size())
        # pygame.display.set_caption(self.window_name)
        self.window.blit(self.surface, (0, 0))
        pygame.display.flip()

    def update_image(self, surface):
        self.surface = surface
        self.resize_image()
        self.window.blit(self.surface, (0, 0))
        pygame.display.flip()

    def append_window_name(self, string):
        pygame.display.set_caption(f'{self.window_name}     {string}')

    def resize_image(self):
        image_width, image_height = self.surface.get_size()
        # Calculate the maximum width and height while preserving the aspect ratio
        max_width = self.window.get_width()
        max_height = self.window.get_height()
        aspect_ratio = image_width / image_height

        scaled_width = int(max_height * aspect_ratio)
        scaled_height = int(max_width / aspect_ratio)

        if scaled_width <= max_width:
            return pygame.transform.scale(self.surface, (scaled_width, max_height))
        else:
            return pygame.transform.scale(self.surface, (max_width, scaled_height))

    def toggle_fullscreen(self):
        self.window = pygame.display.set_mode(self.window.get_size(), pygame.FULLSCREEN if not self.window.get_flags() & pygame.FULLSCREEN else pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE))
        self.window.blit(self.surface, (0, 0))
        pygame.display.flip()

    def start(self):
        self.running = True
        return self.running

    def run(self):
        if self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.running = False
                    elif event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_ALT:
                        self.toggle_fullscreen()
            # self.resize_image()
        return self.running


'''
# Example usage
pygame_surface = pygame.image.load("path_to_image.png")

window = PyGameWindow(pygame_surface)
window.run()
'''
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
import struct
from Args import app_settings
from image_converters import webp_bytearray_to_pil, jpeg_bytearray_to_pil

VIDEO_SIZES = [360, 480, 600, 720, 840, 960, 1200, 1440, 1680, 1920]
WxH_Ratio = 9/16

FRAME_LIMIT = [0, 1/100, 1/75, 1/50, 1/33, 1/25, 1/16, 1/10, 1/6]

PYGAME_WINDOW_MODE = pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE

def clamp_to_array_size(index, array):
    # Ensure index stays within the array range
    if index > len(array)-1:
        index = len(array) - 1
    clamped_index = max(0, index)
    return clamped_index


def frame_rate_up(index):
    return clamp_to_array_size(index - 1, FRAME_LIMIT)


def frame_rate_down(index):
    return clamp_to_array_size(index + 1, FRAME_LIMIT)


def clamp_img_size_oldNFG(index):
    # Ensure index stays within the array range
    if index > len(VIDEO_SIZES)-1:
        index = len(VIDEO_SIZES) - 1
    clamped_index = max(0, index)
    return clamped_index


def image_size_up(index):
    # return clamp_img_size(index + 1)
    return clamp_to_array_size(index + 1, VIDEO_SIZES)


def image_size_down(index):
    # return clamp_img_size(index - 1)
    return clamp_to_array_size(index - 1, VIDEO_SIZES)


class ImageSize:

    def __init__(self):
        self.size_index = 5
        self.value = VIDEO_SIZES[self.size_index]
        self.frame_rate_limit = 5

    def set(self, quality):
        self.size_index = clamp_to_array_size(quality, VIDEO_SIZES)
        self.value = VIDEO_SIZES[self.size_index]

    def up(self):
        self.size_index = image_size_up(self.size_index)
        self.value = VIDEO_SIZES[self.size_index]
        self.report_size()

    def down(self):
        self.size_index = image_size_down(self.size_index)
        self.value = VIDEO_SIZES[self.size_index]
        self.report_size()

    def frame_rate_up(self):
        self.frame_rate_limit = frame_rate_up(self.frame_rate_limit)
        if self.frame_rate_limit > 0:
            app_settings.args.limit = True
        print(f'frame_delay now {FRAME_LIMIT[self.frame_rate_limit]}')

    def frame_rate_down(self):
        self.frame_rate_limit = frame_rate_down(self.frame_rate_limit)
        if self. frame_rate_limit == 0:
            app_settings.args.limit = False
        print(f'frame_delay now {FRAME_LIMIT[self.frame_rate_limit]}')

    def frame_delay(self) -> float:
        return FRAME_LIMIT[self.frame_rate_limit]

    def report_size(self):
        print(f'Outputting video @ {self.value} x {self.value * WxH_Ratio}|{app_settings.args.quality}% quality')



class PyGameOpenGLStreamingWindow:
    def __init__(self, image_pil=None, image_path=None, window_name='Video Stream', geometry=(800, 600), fps_callback=None, callback=None, callback_params=None):
        self.geometry = geometry
        self.window_name = window_name
        self.minimal = False

        self.callback_func = callback
        self.callback_params = callback_params

        self.fps_callback = fps_callback

        # Stream variables initialized to None
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

        # Store the original size of the image
        self.og_img_width, self.og_img_height = self.image.size

        # Initialize Pygame and OpenGL
        pygame.init()
        self.screen = pygame.display.set_mode(self.geometry, PYGAME_WINDOW_MODE)
        pygame.display.set_caption(self.window_name)
        glEnable(GL_TEXTURE_2D)
        self.texture = glGenTextures(1)

        self.init_opengl()

    def init_opengl(self):
        width, height = self.geometry
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(-1, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def update_texture(self):
        img_data = self.image.convert('RGBA').tobytes("raw", "RGBA", 0, -1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.image.width, self.image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

    def draw_image(self):
        self.update_texture()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(1.0, -1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(1.0, 1.0)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glEnd()
        pygame.display.flip()

    def update_image(self):
        if app_settings.fatal_error:
            return
        self.image = self.get_next_frame()
        if self.image is None:
            print('Received image is null')
            app_settings.fatal_error = True
            pygame.quit()
        else:
            self.draw_image()

    def schedule_update(self):
        if app_settings.fatal_error:
            pygame.quit()
            return

        self.update_image()
        if self.callback_func:
            self.callback_func(self.callback_params)

        if self.fps_callback:
            fps = self.fps_callback()
            if fps:
                pygame.display.set_caption(f'{self.window_name}    FPS: {fps:.2f}')

        if self.image is None:
            print('Received image is null')
            app_settings.fatal_error = True
            pygame.quit()
            return

    def init_video_stream(self, client_socket, payload_size):
        self.client_socket = client_socket
        self.payload_size = payload_size

    def get_next_frame(self):
        if self.client_socket is None or self.payload_size is None:
            return self.image
        while len(self.data_holder["data"]) < self.payload_size:
            packet = self.client_socket.recv(4 * 1024)
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

        self.og_img_width, self.og_img_height = frame.size
        return frame

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.VIDEORESIZE:
                self.geometry = event.size
                self.screen = pygame.display.set_mode(self.geometry, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)
                self.init_opengl()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_ALT:
                    self.toggle_fullscreen()
                elif event.key == pygame.K_t and pygame.key.get_mods() & pygame.KMOD_ALT:
                    self.toggle_on_top()
                elif event.key == pygame.K_m and pygame.key.get_mods() & pygame.KMOD_ALT:
                    self.toggle_minimal()
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_ALT:
                    self.resize_to_aspect_ratio()
                elif event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_ALT:
                    self.original_image_size()
                elif event.key == pygame.K_ESCAPE and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.exit_app()

    def toggle_fullscreen(self):
        pygame.display.toggle_fullscreen()

    def original_image_size(self):
        self.geometry = (self.og_img_width, self.og_img_height)
        self.screen = pygame.display.set_mode(self.geometry, PYGAME_WINDOW_MODE)

    def resize_to_aspect_ratio(self):
        current_width, current_height = self.geometry

        if (current_width-self.og_img_width) < (current_height-self.og_img_height):
            # Adjust width based on height
            new_width = int(current_height * (self.og_img_width / self.og_img_height))
            new_height = current_height
        else:
            # Adjust height based on width
            new_width = current_width
            new_height = int(current_width * (self.og_img_height / self.og_img_width))

        self.geometry = (new_width, new_height)
        self.screen = pygame.display.set_mode(self.geometry, PYGAME_WINDOW_MODE)
        self.init_opengl()

    def exit_app(self):
        app_settings.KILLED = True
        print("Program exiting.")
        pygame.quit()
        quit()

    def run(self):
        while True:
            self.handle_events()
            self.schedule_update()


# Replace with actual paths and initialization parameters as needed
# Example:
# window = PyGameOpenGLStreamingWindow(image_path='path_to_image.jpg')
# window.run()

