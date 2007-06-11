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
    def __init__(self, id, x, y):
        id = 1 # XXX we need more images
        pygame.sprite.Sprite.__init__(self)
        self.images = {
            'Up':    load_image('penguin/penguin-%d-right.gif' % id), # XXX
            'Down':  load_image('penguin/penguin-%d-right.gif' % id), # XXX
            'Right': load_image('penguin/penguin-%d-right.gif' % id),
            'Left':  load_image('penguin/penguin-%d-left.gif' % id)}

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
        self.playing = False

        # Inicjalizacja, ustawienie rozdzielczości i tytułu.
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)

        # Ustawienie powtarzania klawiszy.
        pygame.key.set_repeat(200, 30)

    def display_board(self, board):
        """Wyświetl na ekranie pustą planszę.
        """
        self.board = board

        # Utworzenie planszy (będzie niezmienna przez całą grę).
        self.board_surface = BoardSurface(self.board)

        self._repaint()

    def display_penguins(self, id, penguins_positions):
        """Wyświetl pingwiny na ekranie i rozpocznij grę.
        """
        self.penguin_id = id

        self.penguins = {}
        for id, position in enumerate(penguins_positions):
            self.penguins[id] = PenguinSprite(id, *position)

        self.playing = True

        self._repaint()

    def display_text(self, text):
        self.text = text
        self._repaint()

    def move_penguin(self, direction):
        """Przesuń pingwina w podanym kierunku.
        """
        if not self.playing:
            return

        assert direction in ["Up", "Down", "Right", "Left"]

        penguin = self._this_penguin()

        penguin.turn(direction)

        next_location_x = penguin.x
        next_location_y = penguin.y

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
                penguin.x = next_location_x
            if 0 < next_location_y < self.board.y_count - 1:
                penguin.y = next_location_y

        self._repaint()

    def _this_penguin(self):
        return self.penguins[self.penguin_id]

    def _repaint(self):
        """Przerysuj cały ekran.
        """
        self._paint_status_bar()
        self._paint_text()
        if hasattr(self, 'board_surface'):
            self._paint_board()
        if hasattr(self, 'penguins'):
            self._paint_penguins()
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
        self.screen.blit(self.board_surface, (0, STATUS_BAR_HEIGHT))

    def _paint_penguins(self):
        """Wyświetl wszystkie pingwiny.
        """
        for penguin in self.penguins.values():
            assert 0 <= penguin.x < self.board.x_count
            assert 0 <= penguin.y < self.board.y_count

            penguin.paint_on(self.screen)
