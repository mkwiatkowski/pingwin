# -*- coding: utf-8 -*-

from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet import threads

import pygame
from pygame.color import Color


class ClientDisplay(object):
    "Klasa służąca do manipulowania ekranem."

    def __init__(self, title="Penguin"):
        self.width = 300
        self.height = 200
        self.title = title

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)

        self.display_text("Client ready.")

    def display_text(self, text):
        font = pygame.font.Font(None, 36)
        textobj = font.render(text, 1, Color("white"))
        textpos = textobj.get_rect(x=50, y=50)

        self.screen.fill(Color("black"))
        self.screen.blit(textobj, textpos)

        pygame.display.flip()


def get_text_input():
    "Zwróć ciąg znaków reprezentujący ostatnio wciśnięte klawisze."
    while True:
        event = pygame.event.wait()

        if event.type == pygame.QUIT:
            return "Quit"
        elif event.type == pygame.KEYDOWN:
            # Akceptujemy tylko małe litery ASCII.
            if 97 <= event.key <= 122:
                return chr(event.key)


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
            display.display_text("Pressed %s." % data)
            send_to_server_or_exit(data)

        # Zainicuj wątek, który czeka na wejście z klawiatury.
        wait_many_times(on=get_text_input, then=display_and_send)

    def dataReceived(self, data):
        display.display_text("Received %s." % data)


def run():
    global display

    display = ClientDisplay()

    factory = ClientFactory()
    factory.protocol = PenguinClientProtocol

    reactor.connectTCP("localhost", 8888, factory)
    reactor.run()


if __name__ == '__main__':
    run()
