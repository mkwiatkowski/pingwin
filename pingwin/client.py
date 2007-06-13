# -*- coding: utf-8 -*-

import os
import sys
import time

from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet import threads

import pygame

from concurrency import locked, create_lock
from display import ClientDisplay
from board import Board
from helpers import run_after

from messages import *

# Blokada dla wszystkich funkcji klienta.
client_lock = create_lock()

# Zmienne globalne
board        = None
display      = None
player_id    = None
playing      = False


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

def is_movement_key(key):
    return key in ["Up", "Down", "Right", "Left"]

def wait_many_times(on, then):
    """Czekaj aż `on` zwróci wartość, wywołaj `then` i czekaj ponownie.

    Wykonywanie się kończy, gdy `then` rzuci wyjątkiem.
    """
    def do_and_wait_again(data):
        global playing
        try:
            then(data)
        except Exception, e:
            playing = False
            end_game("Exception caught: %s." % e)
            return
        wait_many_times(on, then)

    # Czekaj aż funkcja `on` zwróci wartość i wtedy wywołaj `do_and_wait_again`.
    d = threads.deferToThread(on)
    d.addCallback(do_and_wait_again)

def end_game(reason):
    """Zakończ grę wyświetlając na ekranie powód.
    """
    print reason
    display.display_text(reason)
    run_after(2, lambda: os._exit(1))

class PenguinClientProtocol(Protocol):
    """Klasa służąca do obsługi połączenia z serwerem.
    """

    @locked(client_lock)
    def connectionMade(self):
        """Funkcja wywoływana w momencie nawiązania połączenia z serwerem.

        Tutaj inicjowana jest pętla wait_many_times() działająca na funkcji
        get_text_input() pozwalając użytkownikowi na interakcję z klawiatury.
        """
        @locked(client_lock)
        def take_action_and_send(key):
            global board
            global playing
            global player_id

            # Zakończ program, gdy użytkownik o to prosi.
            if key == "Quit":
                playing = False
                end_game("User quit.")
            # Informację o przesunięciu prześlij do serwera.
            elif is_movement_key(key) and playing:
                turning_makes_sense = display.turning_makes_sense(player_id, key)

                # Najpierw przekręć pingwina na ekranie.
                display.turn_penguin(player_id, key)

                # Spróbuj przesunąć pingwina w wybranym kierunku.
                if board.move_penguin(player_id, key):
                    display.move_penguin(player_id, key)
                    send(self.transport, MoveMeToMessage(key))
                # Jeżeli nie można przesunąć, zobacz czy można chociaż
                # przekręcić.
                elif turning_makes_sense:
                    send(self.transport, TurnMeToMessage(key))

        display.display_text("Connected to server, loading board...")

        # Zainicuj wątek, który czeka na wejście z klawiatury.
        wait_many_times(on=get_text_input, then=take_action_and_send)

    @locked(client_lock)
    def connectionLost(self, reason):
        global playing
        playing = False
        end_game("Disconnected.")

    @locked(client_lock)
    def dataReceived(self, data):
        """Funkcja wywoływana zawsze, gdy otrzymamy dane od serwera.
        """
        messages = receive(data)
        for message in messages:
            self._processMessage(message)

    def _processMessage(self, message):
        global board
        global display
        global player_id
        global playing

        # Pobierz nazwę planszy od serwera, wczytaj ją i pokaż na ekranie.
        if isinstance(message, WelcomeMessage):
            print "Got welcome message from the server."

            board = Board(message.level_name)
            player_id = message.player_id

            display.set_board(board)
            display.display_text("Waiting for other players to join...")

        # Wyświetl pigwiny w pozycjach podanych przez serwer i rozpocznij grę.
        elif isinstance(message, StartGameMessage):
            print "Game started by the server."
            playing = True

            board.set_fishes(message.fishes)
            display.set_fishes(message.fishes)

            board.set_penguins(message.penguins)
            display.set_penguins(message.penguins)

            display.display_text("Go!", duration=1)
            display.set_timer(message.game_duration)

        elif isinstance(message, EndGameMessage):
            print "Game stopped by the server."
            playing = False

            display.stop_timer()
            display.show_results()
            run_after(2, lambda: end_game("Game over."))

        elif isinstance(message, MoveOtherToMessage):
            print "Got moveOtherTo(%s, %s) message." % (message.penguin_id, message.direction)

            display.turn_penguin(message.penguin_id, message.direction)
            display.move_penguin(message.penguin_id, message.direction)
            board.move_penguin(message.penguin_id, message.direction,
                               unconditionally=True)

        elif isinstance(message, TurnOtherToMessage):
            print "Got turnOtherTo(%s, %s) message." % (message.penguin_id, message.direction)
            display.turn_penguin(message.penguin_id, message.direction)

        elif isinstance(message, ScoreUpdateMessage):
            display.update_score(message.penguin_id, message.fish_count)

        # Jeżeli pingwin wpadł do wody to zamigotaj nim przez chwilę.
        elif isinstance(message, PositionUpdateMessage):
            board.update_penguin_position(message.penguin_id, message.x, message.y)
            display.blink_penguin(message.penguin_id)

        elif isinstance(message, NewFishMessage):
            display.add_fish(message.fish)

        elif isinstance(message, RiseGameDurationMessage):
            display.rise_game_duration(message.duration)

        # W innym wypadku po prostu wyświetl otrzymane dane.
        else:
            print "Received %s." % message

class ClientConnection(object):
    """Klasa inicująca połączenie z serwerem.
    """
    def __init__(self, server_address):
        factory = ClientFactory()
        factory.protocol = PenguinClientProtocol
        reactor.connectTCP(server_address, 8888, factory)


def run(server_address):
    global display

    display = ClientDisplay()
    display.display_text("Connecting to server...")
    connection = ClientConnection(server_address)

    # Oddajemy sterowanie do głównej pętli biblioteki Twisted.
    reactor.run()

if __name__ == '__main__':
    try:
        server_address = sys.argv[1]
    except:
        print "usage: %s server_address" % sys.argv[0]

    run(server_address)
