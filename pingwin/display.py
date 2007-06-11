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
        self.images = {
            'Up':    load_image('penguin/penguin-1-right.gif'), # XXX
            'Down':  load_image('penguin/penguin-1-right.gif'), # XXX
            'Right': load_image('penguin/penguin-1-right.gif'),
            'Left':  load_image('penguin/penguin-1-left.gif')}

        # Pingwin na początku patrzy w dół.
        self.image = self.images['Down']
        self.rect = self.image.get_rect()

        self.x = x
        self.y = y

    def paint_on(self, screen):
        """Narysuj siebie na podanym ekranie.
        """
        screen.blit(self.image, self._centered_coordinates())

    def turn(self, direction):
        """Przekręć pingiwna w wybranym kierunku.
        """
        self.image = self.images[direction]

    def _centered_coordinates(self):
        """Zwróć współrzędne, dla których sylwetka pingwina będzie
        wyśrodkowana w jego aktualnym położeniu.
        """
        return (self.x * TILE_WIDTH + 7,
                self.y * TILE_HEIGHT + STATUS_BAR_HEIGHT - 26)


class BoardSurface(pygame.Surface):
    def __init__(self, board):
        pygame.Surface.__init__(self, (TILE_WIDTH * board.x_count,
                                       TILE_HEIGHT * board.y_count))
        self.fill(Color("white"))
        self._init_grounds()

        # Wypełniamy planszę według znaków z mapki poziomu.
        tiles = list(board.level_string)
        for y in range(0, self.get_height(), 40):
            for x in range(0, self.get_width(), 40):
                # Pobierz następną kafelkę.
                tile = tiles.pop(0)
                # Jeżeli w opisie poziomu użyto nieznanej kafelki,
                #   użyj zamiast jej śniegu.
                if tile not in self.ground:
                    tile = ' '
                # Wyświetl kafelkę na planszy.
                self.blit(self.ground[tile], (x, y))

    def _init_grounds(self):
        """Wczytaj obrazki podłoża, zbierając je w słowniku
        self.ground, gdzie klucz odpowiada znakowi użytemu
        na mapce poziomu.
        """
        self.ground = {
            ' ': load_image('ground/snow.gif'),
            '~': load_image('ground/water.gif'),
            '<': load_image('ground/ice-horizontal-left.gif'),
            '-': load_image('ground/ice-horizontal-middle.gif'),
            '>': load_image('ground/ice-horizontal-right.gif'),
            '^': load_image('ground/ice-vertical-top.gif'),
            '/': load_image('ground/ice-vertical-middle.gif'),
            ',': load_image('ground/ice-vertical-bottom.gif')}

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

    def display_board(self, board):
        """Wyświetl planszę na ekranie i umieść na niej pingwina.
        """
        self.board = board

        # Utworzenie planszy (będzie niezmienna przez całą grę).
        self.board_surface = BoardSurface(self.board)

        # Utworzenie pingwina i postawienie go w losowym miejscu na planszy.
        self.penguin = PenguinSprite(*self.board.random_free_tile())

        self._repaint()

    def display_text(self, text):
        self.text = text
        self._repaint()

    def move_penguin(self, direction):
        """Przesuń pingwina w podanym kierunku.
        """
        assert direction in ["Up", "Down", "Right", "Left"]

        self.penguin.turn(direction)

        next_location_x = self.penguin.x
        next_location_y = self.penguin.y

        if direction == "Up":
            next_location_y -= 1
        elif direction == "Down":
            next_location_y += 1
        elif direction == "Right":
            next_location_x += 1
        elif direction == "Left":
            next_location_x -= 1

        # Jeżeli krok skierowany jest w stronę wolnego pola i nie wykracza
        # ono poza planszę, to krok jest wykonywany.
        if self.board.is_free_tile(next_location_x, next_location_y):
            if 0 < next_location_x < self.board.x_count - 1:
                self.penguin.x = next_location_x
            if 0 < next_location_y < self.board.y_count - 1:
                self.penguin.y = next_location_y

        self._repaint()

    def _repaint(self):
        """Przerysuj cały ekran.
        """
        self._paint_status_bar()
        self._paint_text()
        self._paint_board()
        self._paint_penguin()
        pygame.display.flip()

    def _paint_status_bar(self):
        status_bar = pygame.Surface((self.width, STATUS_BAR_HEIGHT))
        self.screen.blit(status_bar, (0,0))

    def _paint_text(self):
        font = pygame.font.Font(None, 36)
        textobj = font.render(self.text, 1, Color("white"))
        textpos = textobj.get_rect(x=50, y=50)

        self.screen.blit(textobj, textpos)

    def _paint_board(self):
        if not hasattr(self, 'board_surface'):
            return

        self.screen.blit(self.board_surface, (0, STATUS_BAR_HEIGHT))

    def _paint_penguin(self):
        """Wyświetl pingwina w pozycji określonej przez jego atrybutu x i y.
        """
        if not hasattr(self, 'penguin'):
            return

        assert 0 <= self.penguin.x < self.board.x_count
        assert 0 <= self.penguin.y < self.board.y_count

        self.penguin.paint_on(self.screen)
