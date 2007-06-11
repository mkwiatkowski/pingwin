# -*- coding: utf-8 -*-

from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor

from board import ServerBoard
from messages import send, receive
from messages import WelcomeMessage, StartGameMessage, EndGameMessage


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

    def connectionMade(self):
        # XXX: użyć wokół całej funkcji locka.

        if Server.game_started:
            print "Client %s rejected, server full." % self.transport.getPeer()
            self.transport.loseConnection()
            return

        print "Client %s connected." % self.transport.getPeer()
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

            # Wyślij wiadomość o rozpoczęciu gry do każdego z klientów.
            for index, transport in enumerate(Server.connected_clients):
                print "Sending start game message to %s." % transport.getPeer()
                send(transport, StartGameMessage(index, penguins_positions))

    def connectionLost(self, reason):
        print "Client %s disconnected." % self.transport.getPeer()
        Server.connected_clients.remove(self.transport)

        # Jeżeli gra była w toku, musimy ją przerwać.
        if Server.game_started:
            for transport in Server.connected_clients:
                print "Sending end game message to %s." % transport.getPeer()
                send(transport, EndGameMessage())

    def dataReceived(self, data):
        """Przekaż dane do wszystkich pozostałych klientów.
        """
        messages = receive(data)

        for message in messages:
            print "Received %s, sending to other." % message
            for transport in Server.connected_clients:
                if transport != self.transport:
                    send(transport, message)


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
