"""Defer terminal signals only across short durability boundaries or model loading."""

import signal
import threading
from contextlib import contextmanager


@contextmanager
def defer_termination():
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
    try:
        yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)
