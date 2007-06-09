import os
import pygame
from pygame.color import Color

DATA_DIR = 'data'


def load_image(name):
    fullname = os.path.join(DATA_DIR, name)

    image = pygame.image.load(fullname)
    image = image.convert_alpha()

    image.set_colorkey(Color("white"))

    return image
