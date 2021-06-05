import youtube_dl

from bot.utils.secToTime import sec2time


class Song():
    def __init__(self, _id: str, _requester: str, _meta={}):
        self.id = _id
        self.requester = _requester
        self.title = _meta.get('title', '')
        self.duration = sec2time(int(_meta.get('duration', 0)))
        self.creator = _meta.get('uploader', '')
        self.thumbnail_url = _meta.get('thumbnail', '')

    def loadInfo(self, songMeta=None):
        if not songMeta:
            try:
                with youtube_dl.YoutubeDL() as ydl:
                    songMeta = ydl.extract_info(f'http://www.youtube.com/watch?v={self.id}', download=False)
            except Exception:
                return False

        self.title = songMeta.get('title', '')
        self.duration = sec2time(int(songMeta.get('duration', 0)))
        self.creator = songMeta.get('uploader', None)
        self.thumbnail_url = songMeta.get('thumbnail', None)
        return True

    def getInfo(self):
        if not (self.title and self.duration and self.creator and self.thumbnail_url):
            try:
                with youtube_dl.YoutubeDL() as ydl:
                    songMeta = ydl.extract_info(f'http://www.youtube.com/watch?v={self.id}', download=False)
                self.title = songMeta.get('title', '')
                self.duration = sec2time(int(songMeta.get('duration', 0)))
                self.creator = songMeta.get('uploader', None)
                self.thumbnail_url = songMeta.get('thumbnail', None)
            except Exception:
                return False

        return {'id': self.id, 'requester': self.requester, 'title': self.title, 'duration': self.duration, 'creator': self.creator, 'thumbnailUrl': self.thumbnail_url}
