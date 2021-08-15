import asyncio
import math
import pickle
from random import shuffle as Mix

import requests
from discord import Colour, Embed, FFmpegPCMAudio, PCMVolumeTransformer, User
from src.bot.bot import Bot
from src.music.queue import Queue
from src.music.song import Song


class VoiceError(Exception):
    pass


class VoiceState():
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    def __init__(self, bot: Bot, guild_id: int) -> None:
        self.bot = bot
        self.guild_id = guild_id
        self.current_song = None
        self.queue = Queue()
        self.previous = Queue()
        self.voice = None
        self.next = asyncio.Event()

        # Load guild settings
        response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                params={'id': guild_id}, headers=self.bot.header).json()
        if response.get('items'):
            self.music_channel_id = response['items'][0]['musicChannelId']
            self._volume = response['items'][0]['volume']/100
            self.timeout = response['items'][0]['timeout']
        else:
            self._volume = 0.5
            self.timeout = 300
            self.music_channel_id = 0
        self._loop_queue = False
        self._loop_song = False

        self.react_message_id = None
        self.react_message_channel_id = None

        self._current = {}
        self._buffer = {}

        self.timestamp = 0

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def is_playing(self) -> bool:
        return self.voice and self.current_song

    async def load_playlist(self, requester: User, playlist_id: int) -> list[Song]:
        with open(f'data/playlists/{playlist_id}.p', 'rb') as f:
            songs = pickle.load(f)
        Mix(songs)
        for song in songs:
            song.requester_name = f'{requester.name}#{requester.discriminator}'
            song.requester_id = requester.id
        return songs

    async def save_playlist(self, playlist_id: int):
        with open(f'data/playlists/{playlist_id}.p', 'wb') as f:
            pickle.dump([self.current_song] + self.queue.get(), f)

    async def get_queue_embed(self, page: int = 1, page_size: int = 10) -> Embed:
        pages = math.ceil(self.queue.get_len()/page_size)
        if page < 1:
            page = 1
        elif page > pages:
            page = pages

        start = (page-1) * page_size
        end = start + page_size

        embed = Embed(title=':scroll: Current Queue:',
                            description='\u200b',
                            color=Colour.blurple())
        embed.set_thumbnail(url=self.bot.logo_url)

        if self.current_song:
            embed.add_field(name='Now playing:',
                            value=f'[{self.current_song.title}]({self.current_song.url})',
                            inline=False)
        if self.queue.get_len():
            for i, song in enumerate(self.queue.get_slice(start, end), start=start):
                embed.add_field(name=f'**`{i+1}.`** {song.title}',
                                value=f'By {song.channel_title}, Duration: {song.duration_str}',
                                inline=False)

            embed.set_footer(text=f'Page {page} of {pages}')
        else:
            embed.add_field(name='Soo empty',
                            value='\u200b')
        return embed

    async def skip(self, index: int = 0):
        if self.is_playing and 0 <= index <= self.queue.get_len()-1:
            self.queue._queue = self.queue._queue[index:]
            self.voice.stop()

    async def play_previous(self):
        if self.current_song:
            self.queue.put_first(self.current_song)

        if self.previous.get_len():
            self.queue.put_first(self.previous.get_at(-1))

        if self.is_playing:
            self.voice.stop()

    async def seek_position(self, position):
        if self.current_song:
            self.timestamp = position
            self.FFMPEG_OPTIONS['options'] = f'-vn -ss {position}'
            self.queue.put_index(self.current_song, 0)

        if self.is_playing:
            self.voice.stop()

    async def shuffle(self):
        self.queue.shuffle()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(f'Voiceerror: {str(error)}')

        self.next.set()

    async def check_if_alone(self):
        if not self.voice:
            return True

        for member in self.voice.channel.members:
            if not member.bot:
                return False
        else:
            return True

    async def create_buffer(self):
        if self.queue.get_len() and self._buffer.get('id') != self.queue.get_first().id and self.queue.get_first().duration:
            self._buffer = {
                'id': self.queue.get_first().id,
                'url': await self.queue.get_first().get_mp3_url()
            }

    async def audio_player_task(self):
        timer = 3
        _timeout = 0
        alone = False
        while True:
            self.next.clear()
            if not self._loop_song:
                while True:
                    alone = await self.check_if_alone()

                    if self.queue.get_len() and not alone:
                        if self.current_song:
                            self.previous.put(self.current_song)
                            if self._loop_queue:
                                self.queue.put(self.current_song)
                        self.current_song = self.queue.pop_first()
                        _timeout = 0
                        break

                    _timeout += timer
                    if _timeout > self.timeout:
                        await self.stop()
                        if self.guild_id in self.bot.voice_states:
                            self.bot.voice_states.pop(self.guild_id)

                        return
                    await asyncio.sleep(timer)

            if self.current_song.duration:
                if self._buffer.get('id') == self.current_song.id:
                    self._current = {
                        'id': self.current_song.id,
                        'url': self._buffer['url']
                    }
                elif self._current.get('id') != self.current_song.id:
                    self._current = {
                        'id': self.current_song.id,
                        'url': await self.current_song.get_mp3_url()
                    }

            if self._current.get('url'):
                self.voice.play(
                    PCMVolumeTransformer(
                        FFmpegPCMAudio(
                            self._current['url'],
                            **self.FFMPEG_OPTIONS),
                        self._volume),
                    after=self.play_next_song)

                if self.timestamp != 0:
                    self.timestamp = 0
                    self.FFMPEG_OPTIONS['options'] = '-vn'

                self.bot.dispatch('playing_song', self)
                await self.create_buffer()
                await self.next.wait()

    async def stop(self):
        self.queue.clear()

        if self.audio_player:
            self.audio_player.cancel()

        if self.react_message_id:
            message = await self.bot.get_channel(self.react_message_channel_id).fetch_message(self.react_message_id)
            await message.clear_reactions()

            self.react_message_id = None
            self.react_message_channel_id = None

        if self.voice:
            await self.voice.disconnect()
            self.voice = None
