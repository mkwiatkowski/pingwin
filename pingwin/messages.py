# -*- coding: utf-8 -*-

import pickle

END_OF_MESSAGE = '\0'


def send(transport, message):
    """Wyślij pojedynczą wiadomość przez podany transport.

    Do wiadomości dołączany jest bajt END_OF_MESSAGE dla oznaczenia końca
    wiadomości.
    """
    transport.write(serialize(message) + END_OF_MESSAGE)

def receive(data):
    """Zwraca listę wiadomości zawartych w przekazanych danych.
    """
    return [ deserialize(msg) for msg in data.split(END_OF_MESSAGE) if msg ]


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
    """Komunikat wysyłany przez serwer do klienta zaraz po nawiązaniu
    połączenia.

    Atrybuty:
      level_name  nazwa poziomu, jaki klient powinien wczytać
    """
    def __init__(self, level_name):
        self.level_name = level_name

class StartGameMessage(Message):
    """Komunikat wysyłany przez serwer do klienta będący znakiem do rozpoczęcia
    rozgrywki.

    Atrybuty:
      penguin_id          identyfikator pingwina należącego do klienta
                          odbierającego tą wiadomość
      penguins_positions  początkowe pozycje wszystkich pingwinów na planszy
    """
    def __init__(self, penguin_id, penguins_positions):
        self.penguin_id = penguin_id
        self.penguins_positions = penguins_positions

class EndGameMessage(Message):
    """Komunikat oznaczający koniec gry.
    """
    pass
