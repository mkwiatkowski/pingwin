# -*- coding: utf-8 -*-

import md5
import os
import time

import pygame
from pygame.color import Color

DATA_DIR = 'data'

#####
# Funkcje ogólne.
#
def make_id_dict(iterable, key='id', function=lambda x:x):
    """Stwórz słownik, którego kluczami są wartości id obiektów
    z danej listy.
    """
    result = {}
    for element in iterable:
        result[getattr(element, key)] = function(element)
    return result

#####
# Funkcje graficzne.
#
def load_image(name):
    fullname = os.path.join(DATA_DIR, name)

    image = pygame.image.load(fullname)
    image = image.convert_alpha()

    image.set_colorkey(Color("white"))

    return image

def level_path(name):
    return os.path.join(DATA_DIR, 'level', name)


#####
# Funkcje sieciowe.
#
def calculate_client_id(transport):
    """Zwróć unikalny identyfikator dla podanego połączenia.
    """
    return md5.md5(str(transport.getPeer()) + str(time.time())).hexdigest()
