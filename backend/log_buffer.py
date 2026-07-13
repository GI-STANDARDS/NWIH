import threading
from collections import deque

_buffer = deque(maxlen=200)
_lock = threading.Lock()


def log(msg: str):
    print(msg)
    with _lock:
        _buffer.append(msg)


def get_logs(count: int = 50) -> list:
    with _lock:
        return list(_buffer)[-count:]


def clear():
    with _lock:
        _buffer.clear()
