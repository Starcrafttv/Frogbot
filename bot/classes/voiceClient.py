import pickle
import random

import discord

from bot.classes.youtubeDl import YoutubeDl


class VoiceClient():
    def __init__(self, _client, _voiceClient):
        self.client = _client
        self.voiceClient = _voiceClient
        self.guildId = _voiceClient.guild.id
        self.volume = 15
        self.currentSong = None
        self.queue = []
        self.previous = []
        self.timeoutMax = 600
        self.timeout = 0
        self.role = None
        self.SpamChannelId = 820710219284742167
        self.reactMessageId = None
        self.reactMessageChannelId = None
        self.UserFollowing = None
        self.UserFollowingSong = None
        self.ydl = YoutubeDl()
        self.playing = False
        self.allInfos = True
        self.loopSong = False
        self.loopQueue = False
        self.following = None
        self.followingQ = None
        self._bufferSong = False

    def loadSavedClient(self, c):
        c.execute(f"SELECT MusicChannelId, Volume, Timeout, ReqRole FROM guilds WHERE GuildID = '{self.guildId}'")
        info = c.fetchone()
        if info:
            self.SpamChannelId = info[0]
            self.volume = info[1]
            self.timeoutMax = info[2]
            self.role = info[3]
            return True
        else:
            return False

    def nextTrack(self):
        if self.queue:
            self.voiceClient.stop()
            self.playing = False
            if self.currentSong:
                self.previous.insert(0, self.currentSong)
            if not self.loopSong:
                self.currentSong = self.queue.pop(0)
            if self.loopQueue:
                self.queue.append(self.currentSong)
            self.startNextSong()

    def previousTrack(self):
        if self.previous:
            self.voiceClient.stop()
            self.playing = False
            if self.currentSong:
                self.queue.insert(0, self.currentSong)
            self.currentSong = self.previous.pop(0)
            self.startNextSong()

    def replay(self):
        if self.currentSong:
            self.voiceClient.stop()
            self.playing = False
            self.startNextSong()

    def loadSongs(self, query: str, requester: str, front: bool = False, skip: bool = False):
        songs = self.ydl.getSongs(query, requester)
        if songs:
            self.allInfos = False
        if front:
            self.queue = songs + self.queue
        else:
            self.queue = self.queue + songs

        if skip or not self.playing:
            self.nextTrack()
        else:
            self.createBufferSong()
        return True

    def skip(self, index: int = 0):
        if self.queue and 0 <= index <= len(self.queue):
            self.queue = self.queue[index:]
            self.nextTrack()
            return True
        return False

    def remove(self, index: int):
        if self.queue and 0 <= index <= len(self.queue):
            self.queue.pop(index)
            self.createBufferSong()
            return True
        return False

    def move(self, fromIndex: int, toIndex: int = 0):
        if self.queue and 0 <= fromIndex <= len(self.queue) and 0 <= toIndex <= len(self.queue):
            song = self.queue.pop(fromIndex)
            self.queue.insert(toIndex, song)
            self.createBufferSong()
            return True
        return False

    def clear(self):
        self.previous = []
        self.queue = []
        return True

    def shuffle(self):
        random.shuffle(self.queue)
        self.createBufferSong()

    def save(self, playlistID):
        with open(f"bot/data/playlists/{playlistID}.p", 'wb') as f:
            pickle.dump([self.currentSong] + self.queue, f)

    def load(self, playlistID, requester):
        with open(f"bot/data/playlists/{playlistID}.p", 'rb') as f:
            songs = pickle.load(f)
        random.shuffle(songs)
        for song in songs:
            song.requester = requester
        if songs:
            self.allInfos = False
        self.queue = self.queue + songs
        if not self.playing:
            self.nextTrack()
        else:
            self.createBufferSong()

    def pause(self):
        self.voiceClient.pause()
        self.playing = False

    def resume(self):
        if self.voiceClient.is_paused():
            self.voiceClient.resume()
            self.playing = True

    def follow(self, userId):
        self.following = userId

        for member in self.voiceClient.channel.members:
            if member.id == self.following:
                for activity in member.activities:
                    if activity.name == "Spotify":
                        requester = f'{member.name}#{member.discriminator}'
                        query = f'{activity.title} {activity.artist}'
                        if query != self.followingQ:
                            self.followingQ = query
                            self.loadSongs(query, requester, True, True)
                        break
                    else:
                        self.following = None
                break
        else:
            self.following = None

    def startNextSong(self):
        if self.ydl.download(self.guildId, self.currentSong.id):
            self.voiceClient.play(discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(f'bot/data/temp/{self.guildId}/song.mp3'), volume=self.volume/100))
            self.playing = True
            for member in self.voiceClient.channel.members:
                if not member.bot:
                    self.timeout = 0
                    break
            if self.SpamChannelId:
                self.client.dispatch('playing_song', self.guildId, self.SpamChannelId, self.currentSong)
            self.createBufferSong()
        else:
            self.nextTrack()

    def createBufferSong(self):
        if not self.loopSong:
            for song in self.queue:
                if self.ydl.download(self.guildId, song.id, True):
                    break
                else:
                    self.queue.remove(song)
