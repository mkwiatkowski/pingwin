# -*- coding: utf-8 -*-

from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet import threads

import pygame
from pygame.color import Color

from helpers import load_image


class PenguinSprite(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = load_image('penguin/penguin-1-right.gif')
        self.rect = self.image.get_rect()

    def centered_at(self, x, y):
        """Zwróć współrzędne, dla których sylwetka pingwina będzie
        wyśrodkowana na polu o współrzędnych lewego górnego rogu x i y.
        """
        return (x + 7, y - 26)


class BoardSurface(pygame.Surface):
    ground_width = 40
    ground_height = 40

    # Plansza składa się z szachownicy 16x10 pól.
    x_count = 16
    y_count = 10

    def __init__(self):
        pygame.Surface.__init__(self, (self.ground_width * self.x_count,
                                       self.ground_height * self.y_count))
        self.fill(Color("white"))

        # Wypełniamy planszę śniegiem.
        snow_image = load_image('ground/snow.gif')
        for x in range(0, self.get_width(), 40):
            for y in range(0, self.get_height(), 40):
                self.blit(snow_image, (x, y))


class ClientDisplay(object):
    "Klasa służąca do manipulowania ekranem."

    # Gra działa w rozdzielczości 640x480.
    width = 640
    height = 480

    # Odległość planszy od górnej granicy ekranu w pikselach.
    status_bar_height = 80

    def __init__(self, title="Penguin"):
        self.title = title

        # Inicjalizacja, ustawienie rozdzielczości i tytułu.
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)

        # Utworzenie planszy (będzie niezmienna przez całą grę).
        self.board = BoardSurface()

        # Utworzenie pingwina.
        self.penguin = PenguinSprite()

        self.display_text("Client ready.")

    def display_text(self, text):
        self.text = text
        self._repaint()

    def _paint_status_bar(self):
        status_bar = pygame.Surface((self.width, self.status_bar_height))
        self.screen.blit(status_bar, (0,0))

    def _paint_text(self):
        font = pygame.font.Font(None, 36)
        textobj = font.render(self.text, 1, Color("white"))
        textpos = textobj.get_rect(x=50, y=50)

        self.screen.blit(textobj, textpos)

    def _repaint(self):
        """Przerysuj cały ekran.
        """
        self._paint_status_bar()
        self._paint_text()
        self._paint_board()
        self._paint_penguin_at(0, 0)
        pygame.display.flip()

    def _paint_board(self):
        self.screen.blit(self.board, (0, self.status_bar_height))

    def _paint_penguin_at(self, x, y):
        """Wyświetl pingwina w pozycji na planszy określonej przez podane
        współrzędne.
        """
        assert 0 <= x < self.board.x_count
        assert 0 <= y < self.board.y_count

        coordinates = self.penguin.centered_at(
            x * self.board.ground_width,
            self.status_bar_height + y * self.board.ground_height)

        self.screen.blit(self.penguin.image, coordinates)


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
