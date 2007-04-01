# -*- coding: utf-8 -*-

from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor


class PenguinServerProtocol(Protocol):
    """Prosty serwer przekazujący dane pomiędzy klientami.
    """
    # Lista obecnie podłączonych klientów.
    connected_clients = []

    def connectionMade(self):
        print "Client connected."
        self.connected_clients.append(self.transport)

    def connectionLost(self, reason):
        print "Client disconnected."
        self.connected_clients.remove(self.transport)

    def dataReceived(self, data):
        """Przekaż dane do wszystkich pozostałych klientów.
        """
        print "Received '%s', sending to other." % data
        for transport in self.connected_clients:
            if transport != self.transport:
                transport.write(data)


def run():
    factory = Factory()
    factory.protocol = PenguinServerProtocol

    reactor.listenTCP(8888, factory)
    reactor.run()


if __name__ == '__main__':
    run()
