"""
Centralized logging system with separate channels.
Each channel maintains its own ring buffer with filtering, severity levels.
"""
import threading
import time
from datetime import datetime
from collections import deque
from typing import Optional


SEVERITY_DEBUG = 0
SEVERITY_INFO = 1
SEVERITY_WARN = 2
SEVERITY_ERROR = 3

SEVERITY_LABELS = {0: "DEBUG", 1: "INFO", 2: "WARN", 3: "ERROR"}


class LogEntry:
    __slots__ = ("timestamp", "channel", "severity", "message", "details")

    def __init__(self, channel: str, severity: int, message: str, details: Optional[dict] = None):
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.channel = channel
        self.severity = severity
        self.message = message
        self.details = details or {}


class Channel:
    def __init__(self, name: str, max_entries: int = 500):
        self.name = name
        self.max_entries = max_entries
        self._entries = deque(maxlen=max_entries)

    def add(self, severity: int, message: str, details: Optional[dict] = None):
        self._entries.append(LogEntry(self.name, severity, message, details))

    def get(self, count: int = 50, severity_min: int = 0, search: str = ""):
        results = list(self._entries)
        if severity_min > 0:
            results = [e for e in results if e.severity >= severity_min]
        if search:
            sl = search.lower()
            results = [e for e in results if sl in e.message.lower()]
        results.reverse()
        return results[:count]

    def clear(self):
        self._entries.clear()

    def count(self):
        return len(self._entries)


class LogSystem:
    def __init__(self):
        self._lock = threading.Lock()
        self._channels: dict[str, Channel] = {}

    def get_channel(self, name: str, max_entries: int = 500) -> Channel:
        with self._lock:
            if name not in self._channels:
                self._channels[name] = Channel(name, max_entries)
            return self._channels[name]

    def log(self, channel: str, severity: int, message: str, details: Optional[dict] = None):
        self.get_channel(channel).add(severity, message, details)

    def debug(self, channel: str, message: str, details: Optional[dict] = None):
        self.log(channel, SEVERITY_DEBUG, message, details)

    def info(self, channel: str, message: str, details: Optional[dict] = None):
        self.log(channel, SEVERITY_INFO, message, details)

    def warn(self, channel: str, message: str, details: Optional[dict] = None):
        self.log(channel, SEVERITY_WARN, message, details)

    def error(self, channel: str, message: str, details: Optional[dict] = None):
        self.log(channel, SEVERITY_ERROR, message, details)

    def get_logs(self, channel: Optional[str] = None, count: int = 50,
                 severity_min: int = 0, search: str = ""):
        with self._lock:
            if channel:
                ch = self._channels.get(channel)
                if not ch:
                    return []
                return [{"timestamp": e.timestamp, "channel": e.channel,
                         "severity": e.severity, "severity_label": SEVERITY_LABELS.get(e.severity, "?"),
                         "message": e.message, "details": e.details}
                        for e in ch.get(count, severity_min, search)]
            all_entries = []
            for ch in self._channels.values():
                for e in ch.get(count, severity_min, search):
                    all_entries.append({"timestamp": e.timestamp, "channel": e.channel,
                                        "severity": e.severity, "severity_label": SEVERITY_LABELS.get(e.severity, "?"),
                                        "message": e.message, "details": e.details})
            all_entries.sort(key=lambda x: x["timestamp"], reverse=True)
            return all_entries[:count]

    def list_channels(self):
        with self._lock:
            return {name: ch.count() for name, ch in self._channels.items()}

    def clear_channel(self, channel: str):
        with self._lock:
            ch = self._channels.get(channel)
            if ch:
                ch.clear()

    def clear_all(self):
        with self._lock:
            for ch in self._channels.values():
                ch.clear()


logs = LogSystem()
