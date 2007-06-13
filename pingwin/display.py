# -*- coding: utf-8 -*-

import time

import pygame
from pygame.color import Color

from helpers import make_id_dict, load_image, make_text, run_after

# Wysokość i szerokość podstawowej kafelki podłoża.
TILE_WIDTH = 40
TILE_HEIGHT = 40

# Odległość planszy od górnej granicy ekranu w pikselach.
STATUS_BAR_HEIGHT = 80


class FishSprite(pygame.sprite.Sprite):
    def __init__(self, fish):
        self.fish = fish

        self._load_images()

        self.image = self.images[fish.type]
        self.rect = self.image.get_rect()

    # Położenie pobieraj z obiektu fish.
    def _getx(self): return self.fish.x
    x = property(_getx)
    def _gety(self): return self.fish.y
    y = property(_gety)

    def paint_on(self, screen):
        """Narysuj siebie na podanym ekranie.
        """
        screen.blit(self.image, self._centered_coordinates())

    def _centered_coordinates(self):
        """Zwróć współrzędne, dla których obrazek rybki będzie wyśrodkowany
        w jego aktualnym położeniu.
        """
        return (self.x * TILE_WIDTH,
                self.y * TILE_HEIGHT + STATUS_BAR_HEIGHT)

    def _load_images(self):
        """Ustaw FishSprite.images, wczytując obrazki z dysku jeżeli to
        konieczne.
        """
        if hasattr(FishSprite, 'images'):
            return

        FishSprite.images = [
            load_image('fish/fish-1.gif'),
            load_image('fish/fish-2.gif'),
            load_image('fish/fish-3.gif'),
            load_image('fish/fish-4.gif')]

class PenguinSprite(pygame.sprite.Sprite):
    def __init__(self, penguin):
        self.penguin = penguin

        id = 1 # penguin.id XXX we need more images
        pygame.sprite.Sprite.__init__(self)
        self.images = {
            'Up':    load_image('penguin/penguin-%d-back.gif' % id),
            'Down':  load_image('penguin/penguin-%d-front.gif' % id),
            'Right': load_image('penguin/penguin-%d-right.gif' % id),
            'Left':  load_image('penguin/penguin-%d-left.gif' % id)}

        # Pingwin na początku patrzy w dół.
        self.image = self.images['Down']
        self.rect = self.image.get_rect()

    # Położenie pobieraj z obiektu penguin.
    def _getx(self): return self.penguin.x
    def _setx(self, x): self.penguin.x = x
    x = property(_getx, _setx)

    def _gety(self): return self.penguin.y
    def _sety(self, y): self.penguin.y = y
    y = property(_gety, _sety)

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
            '#': load_image('ground/wall.gif'),

            '[': load_image('ground/wall-horizontal-left.gif'),
            '=': load_image('ground/wall-horizontal-middle.gif'),
            ']': load_image('ground/wall-horizontal-right.gif'),

            '?': load_image('ground/wall-vertical-top.gif'),
            '|': load_image('ground/wall-vertical-middle.gif'),
            '.': load_image('ground/wall-vertical-bottom.gif'),

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

    def set_board(self, board):
        """Wyświetl na ekranie pustą planszę.
        """
        self.board = board

        # Utworzenie planszy (będzie niezmienna przez całą grę).
        self.board_surface = BoardSurface(self.board)

        self._repaint()

    def set_fishes(self, fishes):
        """Wyświetl rybki na ekranie.
        """
        self.board.set_fishes(fishes)
        self.fishes_sprites = [ FishSprite(fish) for fish in fishes ]
        self._repaint()

    def set_penguins(self, penguins):
        """Wyświetl pingwiny na ekranie i rozpocznij grę.
        """
        self.board.set_penguins(penguins)

        self.penguins_sprites = make_id_dict(penguins, function=PenguinSprite)

        self.playing = True
        self._repaint()

    def set_timer(self, game_duration):
        """Włącz zegar odliczający sekundy do końca gry.
        """
        self.game_start_time = time.time()
        self.game_duration   = game_duration

    def display_text(self, text, duration=None):
        """Pokaż tekst informacyjny na środku ekranu.
        """
        self.text = text
        self._repaint()

        if duration:
            run_after(duration, lambda: self.clear_text())

    def clear_text(self):
        """Wyczyść tekst informacyjny.
        """
        self.text = None
        self._repaint()

    def move_penguin(self, penguin_id, direction):
        """Przesuń pingwina o podanym id w zadanym kierunku.
        """
        if not self.playing:
            return
        assert direction in ["Up", "Down", "Right", "Left"]

        self.board.move_penguin(penguin_id, direction)

        # Przekręć pingwina w odpowiednią stronę.
        self.penguins_sprites[penguin_id].turn(direction)

        # Jeżeli pingwin stanął na polu z rybką, rybka powinna zniknąć.
        fish = self.board.penguin_ate_fish(penguin_id)
        if fish:
            self._remove_fish_sprite(fish)

        self._repaint()

    def update_score(self, penguin_id, fish_count):
        """Uaktualnij wynik gracza i wyświetl go na ekranie.
        """
        self.board.penguins[penguin_id].fish_count = fish_count
        self._repaint()

    def add_fish(self, fish):
        """Dodaj nową rybę na planszę.
        """
        self.board.add_fish(fish)
        self.fishes_sprites.append(FishSprite(fish))
        self._repaint()

    def _remove_fish_sprite(self, fish):
        for index, fish_sprite in enumerate(self.fishes_sprites):
            if fish_sprite.fish == fish:
                self.fishes_sprites.pop(index)
                return

    def _repaint(self):
        """Przerysuj cały ekran.
        """
        self._paint_status_bar()
        if hasattr(self, 'board_surface'):
            self._paint_board()
        if hasattr(self, 'fishes_sprites'):
            self._paint_fishes()
        if hasattr(self, 'penguins_sprites'):
            self._paint_penguins()
        if hasattr(self, 'game_duration'):
            self._paint_timer()
        if self.text:
            self._paint_text()
        pygame.display.flip()

    def _paint_status_bar(self):
        """Przerysuj pasek stanu, nanosząc aktualne wyniki graczy.
        """
        # Nanieś czarne tło. XXX nałożyć ładną bitmapę
        status_bar = pygame.Surface((self.width, STATUS_BAR_HEIGHT))
        self.screen.blit(status_bar, (0,0))

        if not self.playing:
            return

        initial_x = 15
        if len(self.board.penguins) <= 4:
            x_step = 305
        elif len(self.board.penguins) <= 6:
            x_step = 207
        else:
            pass # XXX zrobić inny układ

        x = initial_x
        y = 10
        for index, penguin in enumerate(self.board.penguins.values()):
            text = "Player %d  (%d)" % (index + 1, penguin.fish_count)
            self._blit_text(text, x, y, color=penguin.color)

            x += x_step
            if x + x_step > self.width:
                x = initial_x
                y = 45

    def _paint_text(self):
        font = pygame.font.Font(None, 36)
        text = font.render(self.text, 1, Color("yellow"), Color("black"))

        x = (self.width - text.get_width()) / 2
        y = (self.height - text.get_height()) / 2

        self.screen.blit(text, text.get_rect(x=x, y=y))

    def _paint_board(self):
        """Wyświetl podłoże planszy.
        """
        self.screen.blit(self.board_surface, (0, STATUS_BAR_HEIGHT))

    def _paint_fishes(self):
        """Wyświetl wszystkie rybki.
        """
        for fish in self.fishes_sprites:
            fish.paint_on(self.screen)

    def _paint_penguins(self):
        """Wyświetl wszystkie pingwiny.
        """
        for penguin in self.penguins_sprites.values():
            assert 0 <= penguin.x < self.board.x_count
            assert 0 <= penguin.y < self.board.y_count

            penguin.paint_on(self.screen)

    def _paint_timer(self):
        """Wyświetl zegar.
        """
        elapsed_time      = int(time.time() - self.game_start_time + 0.5)
        remaining_time    = self.game_duration - elapsed_time
        remaining_minutes = remaining_time / 60
        remaining_seconds = remaining_time % 60

        current_time = "%02d:%02d" % (remaining_minutes, remaining_seconds)

        # Zegar normalnie jest zielony; staje się czerwony przez ostatnie
        # 10 sekund.
        color = "green"
        if remaining_time < 10:
            color = "red"

        self._blit_text(current_time, 540, 420, size=36, color=color)

    def _blit_text(self, *args, **kwds):
        self.screen.blit(*make_text(*args, **kwds))
