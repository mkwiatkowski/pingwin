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

########################################################################
# Serwer -> Klient
#
class WelcomeMessage(Message):
    """Komunikat wysyłany przez serwer do klienta zaraz po nawiązaniu
    połączenia.

    Atrybuty:
      player_id   identyfikator przypisany graczowi przez serwer
      level_name  nazwa poziomu, jaki klient powinien wczytać
    """
    def __init__(self, player_id, level_name):
        self.player_id  = player_id
        self.level_name = level_name

class StartGameMessage(Message):
    """Komunikat wysyłany przez serwer do klienta będący znakiem do rozpoczęcia
    rozgrywki.

    Atrybuty:
      penguins       lista pingwinów uczestnicących w grze
      fishes         lista rybek początkowo leżących na planszy
      game_duration  czas trwania partii
    """
    def __init__(self, penguins, fishes, game_duration):
        self.penguins      = penguins
        self.fishes        = fishes
        self.game_duration = game_duration

class EndGameMessage(Message):
    """Komunikat oznaczający koniec gry.
    """
    pass

class MoveOtherToMessage(Message):
    """Komunikat przesyłany z serwera informujący innych graczy o ruchu
    jednego z nich w podanym kierunku.
    """
    def __init__(self, penguin_id, direction):
        self.penguin_id = penguin_id
        self.direction  = direction

class TurnOtherToMessage(Message):
    """Komunikat przesyłany z serwera informujący innych graczy o przekręceniu
    jednego z nich w podanym kierunku.
    """
    def __init__(self, penguin_id, direction):
        self.penguin_id = penguin_id
        self.direction  = direction

class ScoreUpdateMessage(Message):
    """Komunikat przesyłany w momencie, gdy któryś z graczy zdobędzie nową
    lub straci rybkę.
    """
    def __init__(self, penguin_id, fish_count):
        self.penguin_id = penguin_id
        self.fish_count = fish_count

class NewFishMessage(Message):
    """Komunikat przesyłany do klientów w momencie, gdy do planszy dodano
    nową rybkę.
    """
    def __init__(self, fish):
        self.fish = fish

class RiseGameDurationMessage(Message):
    """Komunikat wysyłany do klientów w momencie, gdy gra jest przedłużana.
    """
    def __init__(self, duration):
        self.duration = duration

########################################################################
# Klient -> Serwer
#
class MoveMeToMessage(Message):
    """Komunikat wysyłany przez klienta do serwera informujący o przesunięciu
    pingwina w jednym z czterech dozwolonych kierunków (Up/Down/Right/Left).
    """
    def __init__(self, direction):
        self.direction = direction

class TurnMeToMessage(Message):
    """Komunikat wysyłany przez klienta do serwera informujący o przekręceniu
    pingwina w jednym z czterech dozwolonych kierunków (Up/Down/Right/Left).
    """
    def __init__(self, direction):
        self.direction = direction
