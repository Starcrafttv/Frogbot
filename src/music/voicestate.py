import asyncio
import math
import pickle
import random

from discord import Colour, Embed, FFmpegPCMAudio, PCMVolumeTransformer, User
from src.bot.bot import Bot


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
        self.queue = []
        self.previous = []
        self.voice = None
        self.next = asyncio.Event()

        # Load guild settings
        self.bot.c.execute(
            f"SELECT MusicChannelId, Volume, Timeout FROM guilds WHERE GuildID = {self.guild_id}")
        settings = self.bot.c.fetchone()
        if settings:
            self.music_channel_id = int(settings[0])
            self._volume = int(settings[1])/100
            self.timeout = int(settings[2])
        else:
            self._volume = 0.5
            self.timeout = 300
            self.music_channel_id = 0
        self._loop_queue = False
        self._loop_song = False

        self.react_message_id = None
        self.react_message_channel_id = None
        self.timeout = 180

        self._buffer_id = None
        self._buffer_url = None

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def is_playing(self) -> bool:
        return self.voice and self.current_song

    def load_playlist(self, requester: User, playlist_id: int) -> None:
        with open(f"data/playlists/{playlist_id}.p", 'rb') as f:
            songs = pickle.load(f)
        random.shuffle(songs)
        for song in songs:
            song.requester_name = f'{requester.name}#{requester.discriminator}'
            song.requester_id = requester.id
            self.queue.append(song)

    def save_playlist(self, playlist_id: int):
        with open(f"data/playlists/{playlist_id}.p", 'wb') as f:
            pickle.dump([self.current_song] + self.queue, f)

    def get_queue_embed(self, page: int = 1, page_size: int = 10) -> Embed:
        pages = math.ceil(len(self.queue)/page_size)

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

        for i, song in enumerate(self.queue[start:end], start=start):
            embed.add_field(name=f'**`{i+1}.`** {song.title}',
                            value=f'By {song.channel_title}, Duration: {song.duration_str}',
                            inline=False)

        if len(self.queue):
            embed.set_footer(text=f'Page {page} of {pages}')
        else:
            embed.add_field(name='Soo empty',
                            value='\u200b')
        return embed

    def skip(self):
        if self.is_playing:
            self.voice.stop()

    def play_previous(self):
        if self.current_song:
            self.queue.insert(0, self.current_song)

        if self.previous:
            self.queue.insert(0, self.previous[-1])

        if self.is_playing:
            self.voice.stop()

    def shuffle(self):
        random.shuffle(self.queue)

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    async def audio_player_task(self):
        timer = 3
        _timeout = 0
        alone = False
        while True:
            self.next.clear()
            if not self._loop_song:
                while True:
                    if self.voice:
                        for member in self.voice.channel.members:
                            if not member.bot:
                                alone = False
                                break
                        else:
                            alone = True
                    else:
                        alone = True

                    if len(self.queue) and not alone:
                        if self.current_song:
                            self.previous.append(self.current_song)
                            if self._loop_queue:
                                self.queue.append(self.current_song)
                        self.current_song = self.queue.pop(0)
                        _timeout = 0
                        break

                    _timeout += timer
                    if _timeout > self.timeout:
                        self.bot.loop.create_task(self.stop())
                        return
                    await asyncio.sleep(timer)

            if self._buffer_id == self.current_song.id:
                mp3_url = self._buffer_url
            else:
                mp3_url = await self.current_song.get_mp3_url()

            if mp3_url:
                self.voice.play(
                    PCMVolumeTransformer(
                        FFmpegPCMAudio(
                            mp3_url,
                            **self.FFMPEG_OPTIONS),
                        self._volume),
                    after=self.play_next_song)

                self.bot.dispatch('playing_song', self)
                if len(self.queue) and self._buffer_id != self.current_song.id:
                    self._buffer_url = await self.queue[0].get_mp3_url()
                    if self._buffer_url:
                        self._buffer_id = self.queue[0].id
                await self.next.wait()

    async def stop(self):
        self.queue = []

        if self.voice:
            await self.voice.disconnect()
            self.voice = None
