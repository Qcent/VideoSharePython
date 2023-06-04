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
