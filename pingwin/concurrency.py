# -*- coding: utf-8 -*-

import thread


def create_lock():
    """Utwórz nową blokadę.
    """
    return thread.allocate_lock()

def locked(lock):
    """Dekorator dla funkcji, które mają zakładać blokadę na wejściu
    i zwalniać na wyjściu. Dekorator zapewnia bezwzględne zwolnienie
    blokady niezależnie od sposobu zakończenia wykonania funkcji
    - może to być zarówno normalny powrót, jak i rzucenie wyjątku.
    """
    def locking_function(function):
        def locked_function(*args, **kwds):
            lock.acquire()
            try:
                function(*args, **kwds)
            finally:
                lock.release()
        return locked_function

    return locking_function
