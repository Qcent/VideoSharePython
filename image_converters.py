from PIL import Image
import numpy as np
import cv2
from io import BytesIO
import pygame


def pil_to_pygame(pil_image):
    # Convert the PIL image to RGB mode
    rgb_image = pil_image.convert("RGB")

    # Get the image data as a byte string
    image_data = rgb_image.tobytes()

    # Get the image size
    image_size = rgb_image.size

    # Create a Pygame surface from the image data and size
    pygame_surface = pygame.image.fromstring(image_data, image_size, "RGB")

    return pygame_surface


def cv2_to_pil(cv2_image):
    # Convert the BGR image to RGB
    rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    # Convert the RGB image to PIL Image
    pil_image = Image.fromarray(rgb_image)

    return pil_image


def pil_to_cv2(pil_image):
    # Convert the PIL Image to RGB
    rgb_image = pil_image.convert('RGB')
    # Convert the RGB image to BGR
    bgr_image = cv2.cvtColor(np.array(rgb_image), cv2.COLOR_RGB2BGR)

    return bgr_image


def pil_to_webp_bytearray(pil_image):
    # Convert PIL image to byte array
    byte_array = BytesIO()
    pil_image.save(byte_array, format='WebP')
    byte_array = byte_array.getvalue()

    return byte_array


def webp_bytearray_to_pil(byte_array):
    # Convert byte array to PIL image
    pil_image = Image.open(BytesIO(byte_array))

    return pil_image
