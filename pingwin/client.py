# -*- coding: utf-8 -*-

from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet import threads

import pygame

from display import ClientDisplay


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


class PenguinClientProtocol(Protocol):
    def connectionMade(self):
        def send_to_server_or_exit(data):
            # Zakończ program, gdy użytkownik o to prosi.
            if data == "Quit":
                reactor.stop()
                raise Exception

            self.transport.write(data)

        def display_and_send(data):
            if data in ["Up", "Down", "Right", "Left"]:
                display.move_penguin(data)
            else:
                display.display_text("Pressed %s." % data)
            send_to_server_or_exit(data)

        # Zainicuj wątek, który czeka na wejście z klawiatury.
        wait_many_times(on=get_text_input, then=display_and_send)

    def dataReceived(self, data):
        display.display_text("Received %s." % data)


class ClientConnection(object):
    "Klasa służąca do obsługi połączenia z serwerem."

    def __init__(self):
        factory = ClientFactory()
        factory.protocol = PenguinClientProtocol

        reactor.connectTCP("localhost", 8888, factory)


def run():
    global display
    global connection

    display = ClientDisplay()
    connection = ClientConnection()

    # Oddajemy sterowanie do głównej pętli biblioteki Twisted.
    reactor.run()


if __name__ == '__main__':
    run()
