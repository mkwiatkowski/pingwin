# -*- coding: utf-8 -*-

import pickle


def serialize(object):
    """Zwróć reprezentację obiektu jako ciąg znaków.
    """
    return pickle.dumps(object)

def deserialize(string):
    """Zwróć obiekt zserializowany w podanym stringu.
    """
    return pickle.loads(string)


class Message(object):
    pass

class WelcomeMessage(Message):
    def __init__(self, level_name):
        self.level_name = level_name
