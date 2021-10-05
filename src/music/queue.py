from random import shuffle as mix

from src.music.song import Song


class Queue:
    def __init__(self) -> None:
        self._queue = []

    def get_len(self) -> int:
        return len(self._queue)

    def get_first(self) -> Song:
        if self.get_len():
            return self._queue[0]
        else:
            return None

    def get_at(self, index: int) -> Song:
        if self.get_len():
            return self._queue[index]

    def get_slice(self, start: int, stop: int) -> list[Song]:
        if stop <= self.get_len():
            return self._queue[start:stop]
        else:
            return self._queue[start:]

    def get(self) -> list[Song]:
        return self._queue

    def put(self, arg):
        if isinstance(arg, Song):
            self._queue.append(arg)
        elif isinstance(arg, list):
            self._queue += arg

    def put_first(self, arg):
        if isinstance(arg, Song):
            self._queue.insert(0, arg)
        elif isinstance(arg, list):
            self._queue = arg + self._queue

    def put_index(self, song: Song, index: int):
        self._queue.insert(index, song)

    def remove_first(self):
        if self.get_len():
            self._queue.pop(0)

    def pop(self, index: int) -> Song:
        if self.get_len():
            return self._queue.pop(index)

    def pop_first(self) -> Song:
        if self.get_len():
            return self._queue.pop(0)

    def clear(self):
        self._queue = []

    def shuffle(self):
        mix(self._queue)
