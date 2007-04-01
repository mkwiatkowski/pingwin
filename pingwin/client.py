# -*- coding: utf-8 -*-

from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet import threads


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
            # Gdy linia jest pusta zakończ program.
            if not data:
                reactor.stop()
                raise Exception

            self.transport.write(data)

        # Zainicuj wątek, który czeka na wejście z klawiatury.
        wait_many_times(on=raw_input, then=send_to_server_or_exit)

    def dataReceived(self, data):
        print "RECEIVED %s" % data


def run():
    factory = ClientFactory()
    factory.protocol = PenguinClientProtocol

    reactor.connectTCP("localhost", 8888, factory)
    reactor.run()


if __name__ == '__main__':
    run()
