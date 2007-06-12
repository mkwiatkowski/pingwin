# -*- coding: utf-8 -*-

import thread


global_lock = thread.allocate_lock()

def lock():
    """Załóż blokadę.
    """
    global_lock.acquire()

def unlock():
    """Zwolnij blokadę.
    """
    global_lock.release()

def locked(function):
    """Dekorator dla funkcji, które mają zakładać blokadę na wejściu
    i zwalniać na wyjściu. Dekorator zapewnia bezwzględne zwolnienie
    blokade niezależnie od sposobu zakończenia wykonania funkcji
    - może to być zarówno normalny powrót, jak i rzucenie wyjątku.
    """
    def locked_function(*args):
        lock()
        try:
            function(*args)
        finally:
            unlock()
    return locked_function
