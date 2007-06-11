# -*- coding: utf-8 -*-

import os
import time

from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet import threads

import pygame

from display import ClientDisplay
from board import Board
from messages import send, receive
from messages import WelcomeMessage, StartGameMessage, EndGameMessage


def get_text_input():
    "Zwróć ciąg znaków reprezentujący ostatnio wciśnięte klawisze."
    while True:
        event = pygame.event.wait()

        if event.type == pygame.QUIT:
            return "Quit"
        elif event.type == pygame.KEYDOWN:
            # Akceptujemy tylko klawisz "Escape", strzałki i małe litery ASCII.
            if   event.key == pygame.K_ESCAPE: return "Quit"
            elif event.key == pygame.K_UP:     return "Up"
            elif event.key == pygame.K_DOWN:   return "Down"
            elif event.key == pygame.K_RIGHT:  return "Right"
            elif event.key == pygame.K_LEFT:   return "Left"
            elif 97 <= event.key <= 122:       return chr(event.key)


def wait_many_times(on, then):
    """Czekaj aż `on` zwróci wartość, wywołaj `then` i czekaj ponownie.

    Wykonywanie się kończy, gdy `then` rzuci wyjątkiem.
    """
    def do_and_wait_again(data):
        try:
            then(data)
        except Exception, e:
            end_game("Exception caught: %s." % e)
            return
        wait_many_times(on, then)

    # Czekaj aż funkcja `on` zwróci wartość i wtedy wywołaj `do_and_wait_again`.
    d = threads.deferToThread(on)
    d.addCallback(do_and_wait_again)

def take_action(key):
    """Podejmij odpowiednią akcję na podstawie wciśniętego klawisza.
    """
    if key in ["Up", "Down", "Right", "Left"]:
        display.move_penguin(key)
    else:
        display.display_text("Pressed %s." % key)

def end_game(reason):
    """Zakończ grę wyświetlając na ekranie powód.
    """
    display.display_text(reason)
    time.sleep(2)
    os._exit(1)

class PenguinClientProtocol(Protocol):
    """Klasa służąca do obsługi połączenia z serwerem.
    """

    def connectionMade(self):
        """Funkcja wywoływana w momencie nawiązania połączenia z serwerem.

        Tutaj inicjowana jest pętla wait_many_times() działająca na funkcji
        get_text_input() pozwalając użytkownikowi na interakcję z klawiatury.
        """
        def send_to_server_or_exit(data):
            # Zakończ program, gdy użytkownik o to prosi.
            if data == "Quit":
                end_game("User quit.")

            send(self.transport, data)

        def take_action_and_send(data):
            take_action(data)
            send_to_server_or_exit(data)

        display.display_text("Connected to server, loading board...")

        # Zainicuj wątek, który czeka na wejście z klawiatury.
        wait_many_times(on=get_text_input, then=take_action_and_send)

    def connectionLost(self, reason):
        end_game("Disconnected.")

    def dataReceived(self, data):
        """Funkcja wywoływana zawsze, gdy otrzymamy dane od serwera.
        """
        messages = receive(data)
        for message in messages:
            self._processMessage(message)

    def _processMessage(self, message):
        """Zareaguj na wiadomość.
        """
        # Pobierz nazwę planszy od serwera, wczytaj ją i pokaż na ekranie.
        if isinstance(message, WelcomeMessage):
            print "Got welcome message from the server."
            global board
            board = Board(message.level_name)
            display.display_board(board)
            display.display_text("Waiting for other players to join...")
        # Wyświetl pigwiny w pozycjach podanych przez serwer i rozpocznij grę.
        elif isinstance(message, StartGameMessage):
            print "Game started by the server."
            display.display_penguins(message.penguin_id,
                                     message.penguins_positions)
            display.display_text("Go!")
        elif isinstance(message, EndGameMessage):
            print "Game stopped by the server."
            end_game("Game over.")
        # W innym wypadku po prostu wyświetl otrzymane dane.
        else:
            print "Received %s." % message

class ClientConnection(object):
    """Klasa inicująca połączenie z serwerem.
    """
    def __init__(self):
        factory = ClientFactory()
        factory.protocol = PenguinClientProtocol
        reactor.connectTCP("localhost", 8888, factory)


def run():
    global display
    global connection

    display = ClientDisplay()
    display.display_text("Connecting to server...")
    connection = ClientConnection()

    # Oddajemy sterowanie do głównej pętli biblioteki Twisted.
    reactor.run()

if __name__ == '__main__':
    run()
