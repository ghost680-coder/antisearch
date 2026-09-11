import time
import threading


class TTLCache:
    def __init__(self, ttl=600, max_size=1000):
        self.ttl = ttl
        self.max_size = max_size
        self._store = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            value, expires_at = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key, value, ttl=None):
        with self._lock:
            if len(self._store) >= self.max_size:
                oldest = min(self._store, key=lambda k: self._store[k][1])
                del self._store[oldest]
            self._store[key] = (value, time.time() + (ttl or self.ttl))

    def clear(self):
        with self._lock:
            self._store.clear()

    def size(self):
        with self._lock:
            return len(self._store)
