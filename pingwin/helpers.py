# -*- coding: utf-8 -*-

import md5
import os
import time

from twisted.internet import threads

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

def run_after(duration, function):
    """Uruchom podaną funkcję po upłynięciu zadanego czasu w sekundach.

    Uwaga: funkcja *NIE JEST* otaczana blokadą, należy ją założyć
    samodzielnie w wywoływanej funkcji.
    """
    defered = threads.deferToThread(lambda: time.sleep(duration))
    defered.addCallback(lambda x: function())

def run_each(duration, function, stop_condition):
    """Uruchamiaj podaną funkcję co podany przedział czasu.

    Gdy funkcja stop_condition() zwróci True pętla jest przerywana.
    """
    def call_function_and_defer():
        function()
        if not stop_condition():
            run_each(duration, function, stop_condition)

    run_after(duration, call_function_and_defer)

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

def make_text(text, x, y, size=30, color="white", background=None):
    font = pygame.font.Font(None, size)
    if background:
        text_object = font.render(text, 1, Color(color), Color(background))
    else:
        text_object = font.render(text, 1, Color(color))
    text_position = text_object.get_rect(x=x, y=y)

    return text_object, text_position

def add_name_to_penguin(name, surface, color):
    """Dodaj identyfikator gracza w lewy dolny róg obrazka.
    """
    surface.blit(*make_text(name, 20, 40,
                            size=26,
                            color="white",
                            background=color))

#####
# Funkcje sieciowe.
#
def calculate_client_id(transport):
    """Zwróć unikalny identyfikator dla podanego połączenia.
    """
    return md5.md5(str(transport.getPeer()) + str(time.time())).hexdigest()
