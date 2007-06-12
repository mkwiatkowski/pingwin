# -*- coding: utf-8 -*-

from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor

from board import ServerBoard
from penguin import Penguin

from messages import send, receive
from messages import WelcomeMessage, StartGameMessage, EndGameMessage,\
    MoveMeToMessage, MoveOtherToMessage


class Server(Protocol):
    """Prosty serwer przekazujący dane pomiędzy klientami.

    Konfiguracja odbywa się poprzez przypisanie kilku zmiennym klasowym
    odpowiednich wartości. Dostępne zmienne konfiguracyjne:
      level_name         Nazwa poziomu, na którym będzie odbywać się gra.
      number_of_players  Liczba graczy, która musi się połączyć, by gra mogła
                         się rozpocząć.
    """
    level_name = None
    number_of_players = None

    # Lista obecnie podłączonych klientów.
    connected_clients = []
    # Flaga określająca, czy gra zawiera już wystarczającą liczbę graczy.
    game_started = False
    # Obiekt typu ServerBoard określający obecny stan planszy.
    board = None

    def connectionMade(self):
        # XXX: użyć wokół całej funkcji locka.

        if Server.game_started:
            self.log("Client rejected, server full.")
            self.transport.loseConnection()
            return

        self.log("Client connected from address %s." % self.transport.getPeer())
        Server.connected_clients.append(self.transport)

        # Wyślij wiadomość przywitalną z nazwą planszy.
        send(self.transport, WelcomeMessage(Server.level_name))

        # Rozpocznij grę jeżeli połączyła się wystarczająca liczba graczy.
        if len(Server.connected_clients) == Server.number_of_players:
            print "Got required number of %d players." % Server.number_of_players
            Server.game_started = True

            # Zainicuj planszę i wylosuj położenia pingwinów.
            Server.board = ServerBoard(Server.level_name)
            penguins_positions = Server.board.random_free_tiles(Server.number_of_players)
            Server.board.set_penguins(penguins_positions)

            # Wyślij wiadomość o rozpoczęciu gry do każdego z klientów.
            for index, transport in enumerate(Server.connected_clients):
                self.log("Sending start game message.", transport)
                send(transport, StartGameMessage(index, penguins_positions))

    def connectionLost(self, reason):
        self.log("Client disconnected.")
        Server.connected_clients.remove(self.transport)

        # Jeżeli gra była w toku, musimy ją przerwać.
        if Server.game_started:
            for transport in Server.connected_clients:
                self.log("Sending end game message.", transport)
                send(transport, EndGameMessage())

    def dataReceived(self, data):
        """Funkcja wywoływana zawsze, gdy otrzymamy dane od któregoś z klientów.
        """
        messages = receive(data)
        for message in messages:
            self._processMessage(message)

    def _processMessage(self, message):
        if isinstance(message, MoveMeToMessage):
            # Nie rób nic, jeżeli gra się jeszcze nie rozpoczęła.
            if not Server.game_started:
                return

            # Przesuń pingwina na swojej planszy i jeżeli ruch był poprawny
            # wyślij wiadomość do pozostałych graczy.
            self.log("Received moveTo(%s), sending to other." % message.direction)
            penguin = self._current_penguin()
            if Server.board.move_penguin(penguin, message.direction):
                self._send_to_other(self.transport,
                                    MoveOtherToMessage(penguin.id,
                                                       message.direction))

    def _current_penguin(self):
        """Zwróć pingwina związanego z obecnym połączeniem.
        """
        return Server.board.penguins[self._current_id()]

    def _current_id(self):
        """Identyfikator tego połączenia.
        """
        return self._transport_id(self.transport)

    def _transport_id(self, transport):
        """Identyfikator połączenia związanego z danym transportem.
        """
        # XXX Głupie, ale na razie wystarczy.
        try:
            return Server.connected_clients.index(transport)
        except ValueError:
            return len(Server.connected_clients)

    def _send_to_other(self, transport, message):
        """Wyślij wiadomość do wszystkich klientów poza podanym.
        """
        for transport in Server.connected_clients:
            if transport != self.transport:
                send(transport, message)

    def log(self, message, transport=None):
        if transport is None:
            transport = self.transport
        print "#%d: %s" % (self._transport_id(transport), message)


def run(level_name='default', number_of_players=2):
    """Uruchom serwer obsługujący grę na planszy o podanej nazwie.
    """
    Server.level_name        = level_name
    Server.number_of_players = number_of_players

    factory = Factory()
    factory.protocol = Server

    reactor.listenTCP(8888, factory)
    reactor.run()

if __name__ == '__main__':
    run()
