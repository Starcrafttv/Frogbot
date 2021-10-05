import asyncio
import re

import requests
import spotipy
from aiohttp import ClientSession
from nextcord import User
from emoji import demojize
from googleapiclient.discovery import build
from spotipy.oauth2 import SpotifyClientCredentials
from src.bot.__tokens__ import __tokens__
from src.music.song import Song

youtube = build('youtube', 'v3', developerKey=__tokens__['google'])
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    __tokens__['spotify_client'], __tokens__['spotify']))


async def get_songs(requester: User, query: str) -> list[Song]:
    # Youtube
    if query.find('youtube') != -1:
        # Playlist
        if query.find('list=') != -1:
            playlist_id = query[query.find('list=')+5:]
            if playlist_id.find('&') != -1:
                playlist_id = playlist_id[:playlist_id.find('&')]
            return await get_youtube_playlist(requester, playlist_id)
        # # Video
        if query.find('watch?v=') != -1:
            video_id = query[query.find('watch?v=')+8:]
            if video_id.find('&') != -1:
                video_id = video_id[:video_id.find('&')]
            return await get_youtube_video(requester, [video_id])

    # Spotify
    if query.find('spotify') != -1:
        # Playlist
        if query.find('playlist/') != -1:
            return await get_spotify_playlist(requester, query[query.find('playlist/') + 9:])
        # Video
        return await getSpotifyTrack(requester, query[query.find('track/')+6:])
    # Youtube Search
    return await search_youtube_video(requester, query)


async def get_youtube_playlist(requester: User, playlist_id: str) -> list[Song]:
    playlist = []
    response = {'nextPageToken': None}
    # Go through each playlist page and extract all videos in it
    while True:
        video_ids = []
        if 'nextPageToken' not in response.keys():
            break
        request = youtube.playlistItems().list(
            part='contentDetails, snippet',
            maxResults=50,
            pageToken=response['nextPageToken'],
            playlistId=playlist_id
        )
        response = request.execute()

        if response['items']:
            for video in response['items'][:-1]:
                if video['snippet']['thumbnails']:
                    video_ids.append(video['contentDetails']['videoId'])
        playlist += await get_youtube_video(requester, video_ids)

    return playlist


async def get_youtube_video(requester: User, video_ids: list) -> list[Song]:
    videos = []
    if video_ids:
        id_string = ''.join(video_id + ',' for video_id in video_ids[:-1])
        id_string += video_ids[-1]

        request = youtube.videos().list(
            part='snippet,contentDetails',
            id=id_string
        )
        response = request.execute()
        for video in response['items']:
            videos.append(Song(requester, video))

    return videos


async def search_youtube_video(requester: User, query: str, max_results: int = 1) -> list[Song]:
    url = demojize(f'https://www.youtube.com/results?search_query={query.replace(" ", "+")}&sp=EgIQAQ%253D%253D')
    response = requests.get(url)
    return await get_youtube_video(requester, re.findall(r'watch\?v=(\S{11})', response.text)[:max_results])


async def fetch(url: str, session) -> str:
    async with session.get(demojize(url)) as response:
        html_body = await response.read()
        ids = re.findall(r'watch\?v=(\S{11})', html_body.decode())
        if ids and len(ids):
            return ids[0]
        else:
            return ""


async def youtube_multi_search(queries: list[str]) -> list[str]:
    async with ClientSession() as session:
        tasks = []
        for query in queries:
            url = f'https://www.youtube.com/results?search_query={query.replace(" ", "+")}&sp=EgIQAQ%253D%253D'
            tasks.append(
                asyncio.create_task(
                    fetch(url, session)
                )
            )
        pages = await asyncio.gather(*tasks)
        return list(filter(None, pages))


async def get_spotify_playlist(requester: User, playlist_id: str) -> list[Song]:
    songs = []
    results = sp.playlist(playlist_id)
    tracks = results['tracks']
    items = [await get_track_query(track_meta) for track_meta in tracks['items']]

    while tracks['next']:
        tracks = sp.next(tracks)
        items.extend([await get_track_query(track_meta) for track_meta in tracks['items']])

    ids = await youtube_multi_search(items)
    for x in range(0, len(ids), 50):
        songs.extend(await get_youtube_video(requester, ids[x:x+50]))

    return songs


async def get_track_query(track_meta):
    return f'{track_meta["track"]["name"]} {track_meta["track"]["album"]["artists"][0]["name"]}'


async def getSpotifyTrack(requester: User, track_id: str) -> list[Song]:
    meta = sp.track(track_id)
    track_name = f'{meta["name"]} {meta["album"]["artists"][0]["name"]}'
    return await search_youtube_video(requester, track_name)
