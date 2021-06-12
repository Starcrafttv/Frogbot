from random import shuffle

from src.music.song import Song


class Queue:
    def __init__(self) -> None:
        self._queue = []

    def __len__(self) -> int:
        return len(self._queue)

    def __iter__(self):
        return self._queue.__iter__()

    def add_front(self, song: Song):
        self._queue.insert(0, song)

    def add_back(self, song: Song):
        self._queue.append(song)

    def get(self, index: int):
        if 0 <= index <= len(self._queue):
            return self._queue[index]
        else:
            return None

    def clear(self):
        self._queue = []

    def shuffle(self):
        shuffle(self._queue)

    def remove(self, index: int):
        self._queue.pop(index)
