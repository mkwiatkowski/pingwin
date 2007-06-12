class Penguin(object):
    def __init__(self, id, x, y, color="white"):
        self.id = id
        self.x = x
        self.y = y
        self.color = color

        self.fish_count = 0

    def eat_fish(self):
        self.fish_count += 1
        return self.fish_count
