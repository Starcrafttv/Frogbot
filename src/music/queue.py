from random import shuffle as Mix

from src.music.song import Song


class Queue():
    def __init__(self) -> None:
        self._queue = []
        self._len = 0

    def get_len(self):
        return self._len

    def get_first(self) -> Song:
        if len(self._queue):
            return self._queue[0]
        else:
            return None

    def get_at(self, index: int) -> Song:
        if self._len:
            return self._queue[index]

    def get_slice(self, start: int, stop: int) -> list[Song]:
        if stop < self._len:
            return self._queue[start:stop]

    def get(self) -> list[Song]:
        return self._queue

    def put(self, arg):
        if isinstance(arg, Song):
            self._queue.append(arg)
            self._len += 1
        elif isinstance(arg, list):
            self._queue += arg
            self._len += len(arg)

    def put_first(self, arg):
        if isinstance(arg, Song):
            self._queue.insert(0, arg)
            self._len += 1
        elif isinstance(arg, list):
            self._queue = arg + self._queue
            self._len += len(arg)

    def put_index(self, song: Song, index: int):
        self._queue.insert(index, song)
        self._len += 1

    def remove_first(self):
        if self._len:
            self._len -= 1
            self._queue.pop(0)

    def pop(self, index) -> Song:
        if self._len:
            self._len -= 1
            return self._queue.pop(index)

    def pop_first(self) -> Song:
        if self._len:
            self._len -= 1
            return self._queue.pop(0)

    def clear(self):
        self._queue = []

    def shuffle(self):
        Mix(self._queue)
