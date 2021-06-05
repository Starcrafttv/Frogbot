import os

import spotipy
import youtube_dl
from googleapiclient.discovery import build
from spotipy.oauth2 import SpotifyClientCredentials

from bot.__tokens__ import __tokens__
from bot.classes.song import Song


class YoutubeDl():
    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=__tokens__['google'])
        self.sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
            'a6cc7b005a564ddbb566d7b7adcc7670', __tokens__['spotify']))
        self.ydl_opts = {
            'outtmpl': 'data/temp/song.mp3',
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        self.songId = None
        self.bufferSongId = None

    def download(self, guildId, songId, buffer: bool = False):
        if not os.path.exists(f'bot/data/temp/{guildId}'):
            os.mkdir(f'bot/data/temp/{guildId}')
        if buffer:
            if self.bufferSongId == songId:
                return True
            if os.path.isfile(f'bot/data/temp/{guildId}/buffer.mp3'):
                os.remove(f'bot/data/temp/{guildId}/buffer.mp3')
            self.ydl_opts['outtmpl'] = f'bot/data/temp/{guildId}/buffer.mp3'
            try:
                with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                    ydl.download(['https://www.youtube.com/watch?v=' + songId])
                self.bufferSongId = songId
                return True
            except Exception:
                return False
        else:
            if songId == self.bufferSongId:
                if os.path.isfile(f'bot/data/temp/{guildId}/buffer.mp3'):
                    if os.path.isfile(f'bot/data/temp/{guildId}/song.mp3'):
                        os.remove(f'bot/data/temp/{guildId}/song.mp3')
                    os.rename(f'bot/data/temp/{guildId}/buffer.mp3', f'bot/data/temp/{guildId}/song.mp3')
                    self.bufferSongId = None
                    self.songId = songId
                    return True
            elif songId == self.songId:
                return True
            if os.path.isfile(f'bot/data/temp/{guildId}/song.mp3'):
                os.remove(f'bot/data/temp/{guildId}/song.mp3')
            try:
                self.ydl_opts['outtmpl'] = f'bot/data/temp/{guildId}/song.mp3'
                with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                    ydl.download(['https://www.youtube.com/watch?v=' + songId])
                self.songId = songId
                self.bufferSongId = None
            except Exception:
                return False
            return True

    def getSongs(self, query, requester):
        if not query:
            return []
        elif query.find('youtube') != -1:
            if query.find('list') != -1:
                playlistId = query[query.find('list=')+5:]
                if playlistId.find('&') != -1:
                    playlistId = playlistId[:playlistId.find('&')]
                playlist = self.getYtPlaylist(playlistId, requester)
                if playlist:
                    return playlist
                else:
                    return []
            else:
                songId = query[query.find('watch?v=')+8:]
                if songId.find('&') != -1:
                    songId = songId[:songId.find('&')]
                return [Song(songId, requester)]
        elif query.find('spotify') != -1:
            if query.find('playlist/') != -1:
                return self.getSpotifyPlaylist(query[query.find('playlist/')+9:], requester)
            else:
                return [self.getSpotifyTrack(query[query.find('track/')+6:], requester)]
        return [self.ytSearch(query, 1, requester)]

    def getYtPlaylist(self, playlistId, requester):
        songs = []
        response = {'nextPageToken': None}
        # Go through each playlist page and extract all videos in it
        while True:
            if 'nextPageToken' not in response.keys():
                break
            request = self.youtube.playlistItems().list(
                part='contentDetails',
                maxResults=50,
                pageToken=response['nextPageToken'],
                playlistId=playlistId
            )
            response = request.execute()
            for video in response['items']:
                songs.append(Song(video['contentDetails']['videoId'], requester))
        return songs

    def ytSearch(self, query: str, length: int, requester: str):
        if length == 1:
            with youtube_dl.YoutubeDL() as ydl:
                song_meta = ydl.extract_info('ytsearch:' + query, download=False)['entries'][0]
            return Song(song_meta.get('id', ''), requester, song_meta)
        else:
            songs = []
            request = self.youtube.search().list(
                part='snippet',
                maxResults=length,
                q=query
            )
            response = request.execute()
            for song in response['items']:
                song_ = Song(song['id']['videoId'], requester)
                song_.title = song['snippet']['title']
                song_.creator = song['snippet']['channelTitle']
                song_.thumbnail_url = song['snippet']['thumbnails']['default']['url']
                songs.append(songs)
            return songs

    def getSpotifyPlaylist(self, playlistId: str, requester: str):
        songs = []
        for meta in self.sp.playlist(playlistId)['tracks']['items']:
            trackName = f'{meta["name"]} {meta["album"]["artists"][0]["name"]}'
            songs.append(self.ytSearch(trackName, 1, requester))
        return songs

    def getSpotifyTrack(self, trackId: str, requester: str):
        meta = self.sp.track(trackId)
        trackName = f'{meta["name"]} {meta["album"]["artists"][0]["name"]}'
        return self.ytSearch(trackName, 1, requester)
