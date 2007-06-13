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
        self.fish_count += 1
        return self.fish_count

    def stop(self):
        """Zatrzymaj pingwina.
        """
        self.moving = False

    def _getname(self): return "Player %d" % self.number
    name = property(_getname)
