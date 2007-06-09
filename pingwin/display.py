# -*- coding: utf-8 -*-

import pygame
from pygame.color import Color

from helpers import load_image

# Wysokość i szerokość podstawowej kafelki podłoża.
TILE_WIDTH = 40
TILE_HEIGHT = 40

# Odległość planszy od górnej granicy ekranu w pikselach.
STATUS_BAR_HEIGHT = 80


class PenguinSprite(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = load_image('penguin/penguin-1-right.gif')
        self.rect = self.image.get_rect()

        self.x = x
        self.y = y

    def paint_on(self, screen):
        """Narysuj siebie na podanym ekranie.
        """
        screen.blit(self.image, self._centered_coordinates())

    def _centered_coordinates(self):
        """Zwróć współrzędne, dla których sylwetka pingwina będzie
        wyśrodkowana w jego aktualnym położeniu.
        """
        return (self.x * TILE_WIDTH + 7,
                self.y * TILE_HEIGHT + STATUS_BAR_HEIGHT - 26)


class BoardSurface(pygame.Surface):
    # Plansza składa się z szachownicy 16x10 pól.
    x_count = 16
    y_count = 10

    def __init__(self):
        pygame.Surface.__init__(self, (TILE_WIDTH * self.x_count,
                                       TILE_HEIGHT * self.y_count))
        self.fill(Color("white"))

        # Wypełniamy planszę śniegiem.
        snow_image = load_image('ground/snow.gif')
        for x in range(0, self.get_width(), 40):
            for y in range(0, self.get_height(), 40):
                self.blit(snow_image, (x, y))


class ClientDisplay(object):
    "Klasa służąca do manipulowania ekranem."

    # Gra działa w rozdzielczości 640x480.
    width = 640
    height = 480

    def __init__(self, title="Penguin"):
        self.title = title

        # Inicjalizacja, ustawienie rozdzielczości i tytułu.
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)

        # Ustawienie powtarzania klawiszy.
        pygame.key.set_repeat(200, 30)

        # Utworzenie planszy (będzie niezmienna przez całą grę).
        self.board = BoardSurface()

        # Utworzenie pingwina z podaniem jego pierwotnego położenia.
        self.penguin = PenguinSprite(0, 0)

        self.display_text("Client ready.")

    def display_text(self, text):
        self.text = text
        self._repaint()

    def move_penguin(self, direction):
        """Przesuń pingwina w podanym kierunku.
        """
        assert direction in ["Up", "Down", "Right", "Left"]

        if direction == "Up":
            if self.penguin.y > 0:
                self.penguin.y -= 1
        elif direction == "Down":
            if self.penguin.y < self.board.y_count - 1:
                self.penguin.y += 1
        elif direction == "Right":
            if self.penguin.x < self.board.x_count - 1:
                self.penguin.x += 1
        elif direction == "Left":
            if self.penguin.x > 0:
                self.penguin.x -= 1

        self._repaint()

    def _paint_status_bar(self):
        status_bar = pygame.Surface((self.width, STATUS_BAR_HEIGHT))
        self.screen.blit(status_bar, (0,0))

    def _paint_text(self):
        font = pygame.font.Font(None, 36)
        textobj = font.render(self.text, 1, Color("white"))
        textpos = textobj.get_rect(x=50, y=50)

        self.screen.blit(textobj, textpos)

    def _repaint(self):
        """Przerysuj cały ekran.
        """
        self._paint_status_bar()
        self._paint_text()
        self._paint_board()
        self._paint_penguin()
        pygame.display.flip()

    def _paint_board(self):
        self.screen.blit(self.board, (0, STATUS_BAR_HEIGHT))

    def _paint_penguin(self):
        """Wyświetl pingwina w pozycji określonej przez jego atrybutu x i y.
        """
        assert 0 <= self.penguin.x < self.board.x_count
        assert 0 <= self.penguin.y < self.board.y_count

        self.penguin.paint_on(self.screen)