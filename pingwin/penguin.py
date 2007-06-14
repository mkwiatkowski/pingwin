# -*- coding: utf-8 -*-

class Penguin(object):
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y

        self.fish_count = 0
        self.moving = False
        self.color = "white"
        self.number = 0

    def eat_fish(self):
        """Zjedz rybkę i zwróć ich aktualną liczbę.
        """
        self.fish_count += 1
        return self.fish_count

    def stop(self):
        """Zatrzymaj pingwina.
        """
        self.moving = False

    def drop_into_water(self):
        """Wpadnięcie pingwina do wody oznacza dla niego utratę 5 rybek.

        Funkcja zwraca aktualną liczbę rybek.
        """
        self.fish_count -= 5
        if self.fish_count < 0:
            self.fish_count = 0
        return self.fish_count

    def _getname(self): return "Gracz %d" % self.number
    name = property(_getname)
