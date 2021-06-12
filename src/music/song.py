import re

import discord
import youtube_dl
from discord import Colour, Embed

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}


class Song():
    def __init__(self, requester: discord.User, data: dict) -> None:
        self.requester_name = f'{requester.name}#{requester.discriminator}'
        self.requester_id = requester.id

        self.id = data.get('id')
        snippet = data.get('snippet')
        date = snippet.get('publishedAt')
        self.url = f'http://www.youtube.com/watch?v={self.id}'
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.channel_id = snippet.get('channelId')
        self.channel_title = snippet.get('channelTitle')
        self.title = snippet.get('title')
        self.description = snippet.get('description')
        self.published_at = snippet.get('publishedAt')
        content_details = data.get('contentDetails')
        self.duration = self._yt_duration_to_seconds(content_details.get('duration'))
        self.duration_str = self.sec_to_time(self.duration)
        thumbnails = snippet.get('thumbnails')
        self.thumbnail_url = thumbnails[list(thumbnails.keys())[-1]]['url']

    def create_embed(self) -> Embed:
        embed = (Embed(title=':musical_note: Now playing:',
                       description=f'[{self.title}]({self.url})',
                       color=Colour.blurple())
                 .add_field(name='Requested by', value=self.requester_name)
                 .add_field(name='Duration', value=self.duration_str)
                 .add_field(name='Creator', value=self.channel_title)
                 .set_thumbnail(url=self.thumbnail_url))
        return embed

    async def get_mp3_url(self) -> str:
        try:
            with youtube_dl.YoutubeDL(YTDL_OPTIONS) as ydl:
                data = ydl.extract_info(self.url, download=False)
            return data['url']
        except Exception:
            return ''

    def _yt_duration_to_seconds(self, duration: str) -> int:
        match = re.match('PT(\d+H)?(\d+M)?(\d+S)?', duration).groups()

        seconds = int(match[2].strip('S')) if match[2] else 0
        minutes = int(match[1].strip('M')) if match[1] else 0
        hours = int(match[0].strip('H')) if match[0] else 0
        return seconds + 60 * minutes + 3600 * hours

    @staticmethod
    def sec_to_time(sec: int) -> str:
        # Convert seconds to a normalized string
        m, s = divmod(round(sec), 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        if d > 1:
            if s < 10:
                s = f'0{s}'
            if m < 10:
                m = f'0{m}'
            return f'{d} days, {h}:{m}:{s}'
        elif d == 1:
            if s < 10:
                s = f'0{s}'
            if m < 10:
                m = f'0{m}'
            return f'{d} day, {h}:{m}:{s}'
        elif h > 0:
            if s < 10:
                s = f'0{s}'
            if m < 10:
                m = f'0{m}'
            return f'{h}:{m}:{s}'
        elif m > 0:
            if s < 10:
                s = f'0{s}'
            return f'{m}:{s}'
        else:
            return f'{s}'
