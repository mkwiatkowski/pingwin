# -*- coding: utf-8 -*-
from __future__ import with_statement

import random

from helpers import make_id_dict, level_path


def same_positions(obj1, obj2):
    """Zwróć True jeżeli dwa obiekty są na tej samej pozycji.
    """
    if obj1.x == obj2.x and obj1.y == obj2.y:
        return True
    return False

def is_wall(tile):
    """Zwróc True jeżeli kafelka reprezentuje ścianę.
    """
    return tile in r'?|.[=]#'

def is_water(tile):
    """Zwróc True jeżeli kafelka reprezentuje wodę.
    """
    return tile in r'~'

class Board(object):
    """Plansza, na której rozgrywa się potyczka.

    Atrybuty obiektu:
      level_string   Ciąg znaków reprezentujący układ kafelek na planszy.
                     Patrz niżej po szczegóły dotyczące dozwolonych kafelek.
      blocked_tiles  Lista kafelek, na które nie można wejść.
      water_tiles    Lista kafelek zawierających wodę.

    Dozwolone typy kafelek:
      #  ściana (samotna)
      ?  ściana (górny kraniec)
      |  ściana (pionowa)
      .  ściana (dolny kraniec)
      [  ściana (lewy kraniec)
      =  ściana (pozioma)
      ]  ściana (prawy kraniec)
      <  śliski lód (lewy kraniec)
      -  śliski lód (poziomy)
      >  śliski lód (prawy kraniec)
      ^  śliski lód (górny kraniec)
      /  śliski lód (pionowy)
      ,  śliski lód (dolny kraniec)
      ~  woda
    """
    # Plansza składa się z szachownicy 16x10 pól.
    x_count = 16
    y_count = 10

    def __init__(self, level_name):
        self.level_string  = self._read_level(level_name)

        self.fishes   = []
        self.penguins = {}

        self.blocked_tiles = []
        self.water_tiles   = []

        tiles = list(self.level_string)
        for y in range(self.y_count):
            for x in range(self.x_count):
                tile = tiles.pop(0)
                # Jeżeli kafelka jest ścianą, dodaj jej współrzędne do listy
                # niedostępnych miejsc.
                if is_wall(tile):
                    self.blocked_tiles.append((x, y))
                elif is_water(tile):
                    self.water_tiles.append((x, y))

    def is_free_tile(self, x, y):
        """Zwróc wartość prawda, jeżeli pole o podanych współrzędnych
        jest wolne.
        """
        return (x, y) not in self.blocked_tiles

    def is_unoccupied_tile(self, x, y):
        """Zwróc wartość prawda, jeżeli pole o podanych współrzędnych
        nie jest zajęte, tzn.:
          * nie jest zablokowane (patrz is_free_tile()),
          * nie jest kafelką z wodą (patrz is_water_tile()),
          * nie stoi w tym miejscu - ani pingwin ani rybka.
        """
        if self.is_free_tile(x, y) \
                and not self.is_water_tile(x, y) \
                and not self.occupied_by_fish(x, y) \
                and not self.occupied_by_penguin(x, y):
            return True
        return False

    def is_water_tile(self, x, y):
        """Zwróć wartość prawda, jeżeli pole o podanych współrzędnych
        zawiera kafelkę z wodą.
        """
        return (x, y) in self.water_tiles

    def occupied_by_fish(self, x, y):
        """Zwróć wartość prawda, jeżeli w polu o podanych współrzędnych
        leży rybka.
        """
        for fish in self.fishes:
            if fish.x == x and fish.y == y:
                return True
        return False

    def occupied_by_penguin(self, x, y):
        """Zwróć wartość prawda, jeżeli w polu o podanych współrzędnych
        stoi pingwin.
        """
        for penguin in self.penguins.values():
            if penguin.x == x and penguin.y == y:
                return True
        return False

    def set_fishes(self, fishes):
        self.fishes = fishes

    def set_penguins(self, penguins):
        self.penguins = make_id_dict(penguins)

    def add_fish(self, fish):
        self.fishes.append(fish)

    def move_penguin(self, penguin_id, direction):
        """Przesuń pingwina o podanym id w zadanym kierunku.

        Zwraca True jeżeli ruch był możliwy, False w przeciwnym wypadku.
        """
        assert direction in ["Up", "Down", "Right", "Left"]

        penguin = self.penguins[penguin_id]

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
        if self.is_free_tile(next_location_x, next_location_y):
            if 0 <= next_location_x < self.x_count \
                    and 0 <= next_location_y < self.y_count:
                penguin.x = next_location_x
                penguin.y = next_location_y
                return True

        return False

    def penguin_ate_fish(self, penguin_id):
        """Funkcja zwraca False jeżeli pingwin o podanym id nie stoi na
        żadnej rybce, jeżeli stoi to zwraca obiekt tej rybki i usuwa ją
        z listy self.fishes.
        """
        penguin = self.penguins[penguin_id]

        for index, fish in enumerate(self.fishes):
            if same_positions(penguin, fish):
                return self.fishes.pop(index)

        return False

    def best_fish_count(self):
        """Zwróć ilość rybek, jaką ma najlepszy z graczy.
        """
        best_score = -1

        for penguin in self.penguins.values():
            if penguin.fish_count > best_score:
                best_score = penguin.fish_count

        return best_score

    def _read_level(self, name):
        """Odczytaj dane poziomu o podanej nazwie.
        """
        with open(level_path(name)) as fd:
            # Zwróc zawartość pliku pomijając znaki nowej linii.
            return fd.read().replace("\n", "")

class ServerBoard(Board):
    """Plansza z metodami przydatnymi dla serwera.
    """
    def random_unoccupied_tiles(self, number):
        """Zwróć podaną liczbę niezajętych pól.
        """
        tiles = []
        while len(tiles) != number:
            tile = self.random_unoccupied_tile()
            if tile not in tiles:
                tiles.append(tile)
        return tiles

    def random_unoccupied_tile(self):
        """Zwróć współrzędne losowego niezajętego pola.
        """
        while True:
            x = random.randrange(0, self.x_count)
            y = random.randrange(0, self.y_count)
            if self.is_unoccupied_tile(x, y):
                return (x, y)

    def no_winner(self):
        """Zwróć True jeżeli nie można wyłonić zwycięzcy (np. w przypadku,
        gdy dwoje lub więcej graczy jest równocześnie na pierwszym miejscu).
        """
        best_score = self.best_fish_count()
        players_with_best_score = 0

        for penguin in self.penguins.values():
            if penguin.fish_count == best_score:
                players_with_best_score += 1

        return players_with_best_score > 1
