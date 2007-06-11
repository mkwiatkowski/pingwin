# -*- coding: utf-8 -*-

from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet import threads

import pygame

from display import ClientDisplay
from board import Board
from messages import serialize, deserialize, WelcomeMessage


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
        except:
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
                reactor.stop()
                # Rzucamy wyjątkiem by wyjść z pętli wait_many_times().
                raise Exception

            self.transport.write(serialize(data))

        def take_action_and_send(data):
            take_action(data)
            send_to_server_or_exit(data)

        display.display_text("Connected.")

        # Zainicuj wątek, który czeka na wejście z klawiatury.
        wait_many_times(on=get_text_input, then=take_action_and_send)

    def dataReceived(self, data):
        """Funkcja wywoływana zawsze, gdy otrzymamy dane od serwera.
        """
        message = deserialize(data)

        # Pobierz nazwę planszy od serwera, wczytaj ją i pokaż na ekranie.
        if isinstance(message, WelcomeMessage):
            global board
            board = Board(message.level_name)
            display.display_board(board)
        # W innym wypadku po prostu wyświetl otrzymane dane.
        else:
            display.display_text("Received %s." % message)

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
