# -*- coding: utf-8 -*-

import time

import pygame
from pygame.color import Color

from concurrency import locked, create_lock
from helpers import make_id_dict, load_image, make_text, run_after, run_each,\
    add_name_to_penguin

# Wysokość i szerokość podstawowej kafelki podłoża.
TILE_WIDTH = 40
TILE_HEIGHT = 40

# Odległość planszy od górnej granicy ekranu w pikselach.
STATUS_BAR_HEIGHT = 80

# Blokada dla wszystkich funkcji wyświetlających.
display_lock = create_lock()


class FishSprite(pygame.sprite.Sprite):
    def __init__(self, fish):
        pygame.sprite.Sprite.__init__(self)

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
    # Liczba klatek z jakiej składa się animacja pingwina.
    number_of_frames = 6

    def __init__(self, penguin):
        pygame.sprite.Sprite.__init__(self)

        self.penguin = penguin

        self._load_images()

        # Na początku pingwin stoi w miejscu patrząc w dół.
        self.direction = "Down"
        self.current_frame = 0
        self._set_image()

    # Informację o tym, czy pingwin właśnie się przesuwa pobieraj z obiektu
    # penguin.
    def _getmoving(self): return self.penguin.moving
    moving = property(_getmoving)

    def paint_on(self, screen):
        """Narysuj siebie na podanym ekranie.
        """
        screen.blit(self.image, self._centered_coordinates())

    def turn(self, direction):
        """Przekręć pingiwna w wybranym kierunku.
        """
        self.direction = direction
        self._set_image()

    def animate_move(self, direction):
        """Zanimuj przejście pingwina w wybranym kierunku.
        """
        self._set_image()

    def flip(self):
        """Zamień obrazek na następną klatkę animacji.
        """
        self.current_frame += 1
        self._set_image()

        # Jeżeli pokazaliśmy wszystkie klatki to zakończ animację.
        if self._is_last_frame():
            self.current_frame = 0
            self.penguin.stop()

    def _is_last_frame(self):
        """Zwróć wartość prawda jeżeli wyświetlamy ostatnią klatkę animacji.
        """
        return self.current_frame == self.number_of_frames - 1

    def _remaining_frames(self):
        """Zwróć liczbę klatek, jakie jeszcze będziemy musieli wyświetlić.
        """
        return self.number_of_frames - self.current_frame

    def _centered_coordinates(self):
        """Zwróć współrzędne, dla których sylwetka pingwina będzie
        wyśrodkowana w jego aktualnym położeniu.
        """
        # Liczba pikseli przesunięcia dla jednej klatki.
        frame_step = TILE_WIDTH / self.number_of_frames

        centered_x = self.penguin.x * TILE_WIDTH + 7
        centered_y = self.penguin.y * TILE_HEIGHT + STATUS_BAR_HEIGHT - 26

        # Jeżeli się poruszamy to self.penguin.x i self.penguin.y wskazują
        # na klatkę docelową.
        if self.moving:
            if self.direction == "Right":
                centered_x -= frame_step * self._remaining_frames()
            elif self.direction == "Left":
                centered_x += frame_step * self._remaining_frames()
            elif self.direction == "Up":
                centered_y += frame_step * self._remaining_frames()
            elif self.direction == "Down":
                centered_y -= frame_step * self._remaining_frames()

        return centered_x, centered_y

    def _load_images(self):
        """Ustaw PenguinSprite.images, wczytując obrazki z dysku jeżeli to
        konieczne.
        """
        id = 1 # XXX na razie tylko jeden typ/kolor pingwina

        def frames_in_direction(direction):
            frames = []

            for frame in range(1, self.number_of_frames+1):
                # Wczytaj klatkę z dysku.
                frame = load_image('penguin/penguin-%d-%s-%d.gif' % (id, direction, frame))
                # Nanieś na klatkę identyfikator gracza.
                add_name_to_penguin(frame)
                # Dodaj klatkę do listy.
                frames.append(frame)

            return frames

        self.images = {
            'Up':    frames_in_direction("back"),
            'Down':  frames_in_direction("front"),
            'Right': frames_in_direction("right"),
            'Left':  frames_in_direction("left")}

    def _set_image(self):
        """Ustaw obrazek pingwina zależnie od obecnego kierunku i klatki
        animacji.
        """
        self.image = self.images[self.direction][self.current_frame]
        self.rect = self.image.get_rect()

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

        # Inicjalizacja, ustawienie rozdzielczości i tytułu.
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)

        # Ustawienie powtarzania klawiszy.
        pygame.key.set_repeat(200, 30)

        self.text = None

        # Zacznij odświeżać ekran z domyślną częstotliwością.
        refresh_it(self)

    @locked(display_lock)
    def set_board(self, board):
        """Wyświetl na ekranie pustą planszę.
        """
        self.board = board

        # Utworzenie planszy (będzie niezmienna przez całą grę).
        self.board_surface = BoardSurface(self.board)

    @locked(display_lock)
    def set_fishes(self, fishes):
        """Wyświetl rybki na ekranie.
        """
        self.fishes_sprites = [ FishSprite(fish) for fish in fishes ]

    @locked(display_lock)
    def set_penguins(self, penguins):
        """Wyświetl wszystkie pingwiny na ekranie.
        """
        self.penguins_sprites = make_id_dict(penguins, function=PenguinSprite)

    @locked(display_lock)
    def set_timer(self, game_duration):
        """Włącz zegar odliczający sekundy do końca gry.
        """
        self.game_start_time = time.time()
        self.game_duration   = game_duration

    @locked(display_lock)
    def display_text(self, text, duration=None):
        """Pokaż tekst informacyjny na środku ekranu.

        Jeżeli podano parametr `duration` napis zniknie po zadanej liczbie
        sekund.
        """
        self.text = text

        if duration:
            run_after(duration, lambda: self.clear_text())

    @locked(display_lock)
    def clear_text(self):
        """Wyczyść tekst informacyjny.
        """
        self.text = None

    @locked(display_lock)
    def turn_penguin(self, penguin_id, direction):
        """Przekręć pingwina w wybranym kierunku.

        Zwraca True, gdy przekręcenie się miało sens (tzn. wcześniej
        pingwin był skierowany w innym kierunku i nie był w trakcie ruchu).
        """
        penguin = self.penguins_sprites[penguin_id]

        if not penguin.moving:
            penguin.turn(direction)

    @locked(display_lock)
    def turning_makes_sense(self, penguin_id, direction):
        """Zwróć True, gdy przekręcenie danego pingwina w zadanym kierunku
        ma sens, tzn.:
          * wcześniej pingwin był skierowany w innym kierunku
          * nie był w trakcie ruchu
        """
        penguin = self.penguins_sprites[penguin_id]

        if not penguin.moving and penguin.direction != direction:
            return True

        return False

    @locked(display_lock)
    def move_penguin(self, penguin_id, direction):
        """Przesuń pingwina o podanym id w zadanym kierunku.
        """
        self.penguins_sprites[penguin_id].animate_move(direction)

        # Jeżeli pingwin stanął na polu z rybką, rybka powinna zniknąć.
        fish = self.board.penguin_ate_fish(penguin_id)
        if fish:
            self._remove_fish_sprite(fish)

    @locked(display_lock)
    def update_score(self, penguin_id, fish_count):
        """Uaktualnij wynik gracza i wyświetl go na ekranie.
        """
        self.board.penguins[penguin_id].fish_count = fish_count

    @locked(display_lock)
    def add_fish(self, fish):
        """Dodaj nową rybę na planszę.
        """
        self.board.add_fish(fish)
        self.fishes_sprites.append(FishSprite(fish))

    @locked(display_lock)
    def rise_game_duration(self, duration):
        """Przedłuż czas trwania gry o podaną liczbę sekund.
        """
        self.game_duration += duration

    @locked(display_lock)
    def stop_timer(self):
        """Zatrzymaj zegar.
        """
        del self.game_duration

    @locked(display_lock)
    def refresh(self):
        """Przerysuj cały ekran.
        """
        if hasattr(self, 'penguins_sprites'):
            self._paint_status_bar()
        if hasattr(self, 'board_surface'):
            self._paint_board()
        if hasattr(self, 'fishes_sprites'):
            self._paint_fishes()
        if hasattr(self, 'penguins_sprites'):
            self._flip_penguins_animations()
            self._paint_penguins()
        if hasattr(self, 'game_duration'):
            self._paint_timer()
        if self.text:
            self._paint_text()

        pygame.display.flip()

    # Tej funkcji nie blokujemy, bo ona tylko owija metodę display_lock(),
    # która sama zakłada blokadę.
    def show_results(self):
        """Wyświetl na ekranie kto zwycieżył tę potyczkę.
        """
        self.display_text("Player %d won!" % self._winner_id())

    def _winner_id(self):
        """Znajdź identyfikator zwycięskiego gracza.
        """
        winner_id = -1
        max_score = -1

        for index, penguin in enumerate(self.board.penguins.values()):
            if penguin.fish_count > max_score:
                winner_id = index
                max_score = penguin.fish_count

        # Identyfikatory graczy zaczynają się od 1, nie od 0.
        return winner_id + 1

    def _remove_fish_sprite(self, fish):
        """Usuń z planszy sprite reprezentujący daną rybkę.
        """
        for index, fish_sprite in enumerate(self.fishes_sprites):
            if fish_sprite.fish == fish:
                self.fishes_sprites.pop(index)
                return

    def _paint_status_bar(self):
        """Przerysuj pasek stanu, nanosząc aktualne wyniki graczy.
        """
        # Nanieś czarne tło. XXX nałożyć ładną bitmapę
        status_bar = pygame.Surface((self.width, STATUS_BAR_HEIGHT))
        self.screen.blit(status_bar, (0,0))

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
        """Wyświetl tekst zawarty w atrybucie self.text na środku ekranu.
        """
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

    def _flip_penguins_animations(self):
        """Przestaw klatki w animacji wszystkich poruszających się pingwinów.
        """
        for penguin in self.penguins_sprites.values():
            if penguin.moving:
                penguin.flip()

    def _paint_penguins(self):
        """Wyświetl wszystkie pingwiny.
        """
        for penguin in self.penguins_sprites.values():
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

def refresh_it(display, fps=30):
    """Rozpocznij odświeżanie podanego ekranu z podaną częstotliwością
    (domyślnie 30 klatek/sekundę). Jedyna metoda jaką musi obsługiwać
    obiekt `display` to refresh().
    """
    run_each(1.0/fps,
             lambda: display.refresh(),
             lambda: False)
