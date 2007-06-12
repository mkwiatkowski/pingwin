import random

class Fish(object):
    def __init__(self, type, x, y):
        self.type = type
        self.x = x
        self.y = y

    @classmethod
    def random_type(cls):
        return random.randint(0, 3)
