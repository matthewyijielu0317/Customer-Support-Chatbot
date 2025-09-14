from collections import OrderedDict
from typing import Generic, MutableMapping, Optional, Tuple, TypeVar


K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    def __init__(self, capacity: int = 256):
        self.capacity = capacity
        self.store: MutableMapping[K, V] = OrderedDict()

    def get(self, key: K) -> Optional[V]:
        if key not in self.store:
            return None
        self.store.move_to_end(key)
        return self.store[key]

    def put(self, key: K, value: V) -> None:
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = value
        if len(self.store) > self.capacity:
            self.store.popitem(last=False)


