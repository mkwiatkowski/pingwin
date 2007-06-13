# -*- coding: utf-8 -*-

import signal
import time
import os
import sys

from itertools import cycle

from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor

from board import ServerBoard
from fish import Fish
from penguin import Penguin
from concurrency import locked
from helpers import calculate_client_id, run_each, run_after

from messages import send, receive
from messages import WelcomeMessage, StartGameMessage, EndGameMessage,\
    MoveMeToMessage, MoveOtherToMessage, ScoreUpdateMessage, NewFishMessage,\
    RiseGameDurationMessage, TurnMeToMessage, TurnOtherToMessage


class Server(Protocol):
    """Prosty serwer przekazujący dane pomiędzy klientami.

    Konfiguracja odbywa się poprzez przypisanie kilku zmiennym klasowym
    odpowiednich wartości. Dostępne zmienne konfiguracyjne:
      level_name         Nazwa poziomu, na którym będzie odbywać się gra.
      number_of_players  Liczba graczy, która musi się połączyć, by gra mogła
                         się rozpocząć.
      number_of_fishes   Liczba rybek jaka zostanie początkowo umieszczona
                         na planszy. Jest to jednocześnie maksymalna liczba
                         rybek, jaka może znaleźć się na planszy.
      new_fish_delay     Liczba sekund jaka musi upłynąć zanim zostaną dodane
                         nowe rybki.
      game_duration      Limit czasu gry w sekundach. Uwaga: rozgrywka może
                         trwać więcej niż podany tutaj czas, patrz metoda
                         _end_game().
    """
    level_name        = None
    number_of_players = None
    number_of_fishes  = None
    new_fish_delay    = None

    # Słownik obecnie podłączonych klientów.
    connected_clients = {}
    # Flaga określająca, czy gra zawiera już wystarczającą liczbę graczy.
    game_started = False
    # Obiekt typu ServerBoard określający obecny stan planszy.
    board = None

    @locked
    def connectionMade(self):
        # Wygeneruj unikalny identyfikator klienta i zapamiętaj go.
        client_id = calculate_client_id(self.transport)
        self.transport.client_id = client_id

        if Server.game_started:
            self.log("Client rejected, server full.")
            self.transport.loseConnection()
            return

        self.log("Client connected from address %s." % self.transport.getPeer())
        Server.connected_clients[client_id] = self.transport

        # Wyślij wiadomość przywitalną z nazwą planszy.
        send(self.transport, WelcomeMessage(client_id, Server.level_name))

        # Rozpocznij grę jeżeli połączyła się wystarczająca liczba graczy.
        if len(Server.connected_clients) == Server.number_of_players:
            print "Got required number of %d players." % Server.number_of_players
            self._init_game()

    @locked
    def connectionLost(self, reason):
        self.log("Client disconnected.")
        Server.connected_clients.pop(self.transport.client_id)

        # Jeżeli gra była w toku, musimy ją przerwać.
        self._end_game(right_now=True)

    @locked
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
            client_id = self.transport.client_id
            self.log("Received moveTo(%s)." % message.direction)

            if Server.board.move_penguin(client_id, message.direction):
                self._send_to_other(MoveOtherToMessage(client_id, message.direction))
                if Server.board.penguin_ate_fish(client_id):
                    new_fish_count = Server.board.penguins[client_id].eat_fish()
                    self._send_to_all(ScoreUpdateMessage(client_id, new_fish_count))

                # Server.board.move_penguin ustawiło flagę 'moving', zwolnij ją
                # po 0.1 sekundy (zapezpiecza przed botami).
                run_after(0.1, lambda: Server.board.penguins[client_id].stop())
            else:
                self.log("Illegal move.")

        elif isinstance(message, TurnMeToMessage):
            client_id = self.transport.client_id
            self.log("Received turnTo(%s)." % message.direction)

            self._send_to_other(TurnOtherToMessage(client_id, message.direction))

    def _send_to_all(self, message):
        """Wyślij wiadomość do wszystkich klientów.
        """
        for transport in Server.connected_clients.values():
            self.log_message(message, transport)
            send(transport, message)

    def _send_to_other(self, message):
        """Wyślij wiadomość do wszystkich klientów poza obecnym
        (czyli `self.transport`).
        """
        for transport in Server.connected_clients.values():
            if transport.client_id != self.transport.client_id:
                self.log_message(message, transport)
                send(transport, message)

    def _end_game(self, right_now=False):
        """Zakończ rozgrywkę.

        Jeżeli `right_now` nie jest równy True gra nie zakończy się dopóki
        gra nie ma rozstrzygnięcia (tzn. nie ma jednego zwycięskiego gracza).
        """
        if not Server.game_started:
            return

        # Dolicz 10 sekund ekstra
        if not right_now and Server.board.no_winner():
            self._send_to_all(RiseGameDurationMessage(10))
            run_after(10, lambda: self._end_game())
            return

        self._send_to_all(EndGameMessage())
        Server.game_started = False

    def _init_game(self):
        """Zainicjuj wszystkie potrzebne struktury i rozpocznij grę wysyłając
        wszystkim graczom komunikat StartGameMessage.
        """
        # Zainicuj planszę.
        Server.board = ServerBoard(Server.level_name)

        # Wylosuj położenia pingwinów i rybek.
        tiles_to_allocate  = Server.number_of_players + Server.number_of_fishes
        unoccupied_tiles   = Server.board.random_unoccupied_tiles(tiles_to_allocate)
        penguins_positions = unoccupied_tiles[:Server.number_of_players]
        fishes_positions   = unoccupied_tiles[Server.number_of_players:]

        # Ustaw pingwiny na planszy.
        penguins = []
        for client_id, position in zip(Server.connected_clients.keys(),
                                       penguins_positions):
            penguins.append(Penguin(client_id, *position))
        Server.board.set_penguins(penguins)

        # Ustaw rybki na planszy.
        fishes = []
        for type, position in zip(cycle(range(4)), fishes_positions):
            fishes.append(Fish(type, *position))
        Server.board.set_fishes(fishes)

        # Wyślij wiadomość o rozpoczęciu gry do każdego z klientów.
        self._send_to_all(StartGameMessage(penguins, fishes, Server.game_duration))

        Server.game_started = True
        self._start_adding_fishes()
        self._start_timer()

    def _start_adding_fishes(self):
        """Funkcja inicjująca dodawanie co jakiś czas nowych rybek do planszy.
        """
        def try_to_add_a_fish():
            # Nie dodajemy nowych rybek do zakończonej gry.
            if Server.game_started is False:
                return

            # Nie dodajemy nowych rybek keżeli na planszy leży ich
            # wystarczająca ilość.
            if len(Server.board.fishes) >= Server.number_of_fishes:
                return

            # Wylosuj typ i położenie nowej rybki.
            type     = Fish.random_type()
            position = Server.board.random_unoccupied_tile()

            # Utwórz rybkę i dodaj ją do planszy.
            fish = Fish(type, *position)
            Server.board.add_fish(fish)

            # Wyślij do wszystkich klientów powiadomienie o nowej rybce.
            self._send_to_all(NewFishMessage(fish))

        def stop_condition():
            return Server.game_started is False

        # Zainicjuj wykonywanie tej funkcji co Server.new_fish_delay sekund.
        run_each(Server.new_fish_delay, try_to_add_a_fish, stop_condition)

    def _start_timer(self):
        """Funkcja inicjująca licznik do zakończenia rozgrywki.
        """
        run_after(Server.game_duration, lambda: self._end_game())

    def log(self, message, transport=None):
        """Wyświetl wiadomość dotyczącą podanego (lub obecnie obsługiwanego) klienta.
        """
        if transport is None:
            transport = self.transport
        print "#%s..: %s" % (transport.client_id[:4], message)

    def log_message(self, message, transport=None):
        """Wyświetl wiadomość dotyczącą podanego komunikatu.
        """
        self.log("Sending %s." % type(message).__name__, transport)

def close_server_by_signal(signal_number, stack_frame):
    print "User requested exit."
    reactor.stop()
    time.sleep(1)
    os._exit(0)

def run(level_name='default', number_of_players=2, number_of_fishes=7,
        new_fish_delay=2, game_duration=60):
    """Uruchom serwer obsługujący grę na planszy o podanej nazwie.
    """
    Server.level_name        = level_name
    Server.number_of_players = number_of_players
    Server.number_of_fishes  = number_of_fishes
    Server.new_fish_delay    = new_fish_delay
    Server.game_duration     = game_duration

    factory = Factory()
    factory.protocol = Server

    # Zarejestruj obsługę sygnału kończącego (Ctrl-C).
    signal.signal(signal.SIGINT, close_server_by_signal)

    reactor.listenTCP(8888, factory)

    print "Server started. Waiting for connections..."
    reactor.run()

if __name__ == '__main__':
    try:
        number_of_players = int(sys.argv[1])
        game_duration     = int(sys.argv[2])
    except:
        print "usage: %s number_of_players game_duration" % sys.argv[0]
        sys.exit()

    run(number_of_players=number_of_players, game_duration=game_duration)
