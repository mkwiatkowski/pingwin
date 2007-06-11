# -*- coding: utf-8 -*-

from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor

from messages import serialize, deserialize, WelcomeMessage


class PenguinServerProtocol(Protocol):
    """Prosty serwer przekazujący dane pomiędzy klientami.
    """
    # Lista obecnie podłączonych klientów.
    connected_clients = []

    def connectionMade(self):
        print "Client connected."
        self.connected_clients.append(self.transport)

        # Wyślij wiadomość przywitalną z nazwą planszy.
        self.transport.write(serialize(WelcomeMessage('default')))

    def connectionLost(self, reason):
        print "Client disconnected."
        self.connected_clients.remove(self.transport)

    def dataReceived(self, data):
        """Przekaż dane do wszystkich pozostałych klientów.
        """
        print "Received '%s', sending to other." % deserialize(data)
        for transport in self.connected_clients:
            if transport != self.transport:
                transport.write(data)


def run(level_name='default'):
    """Uruchom serwer obsługujący grę na planszy o podanej nazwie.
    """
    factory = Factory()
    factory.protocol = PenguinServerProtocol

    reactor.listenTCP(8888, factory)
    reactor.run()

if __name__ == '__main__':
    run()
