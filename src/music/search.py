import spotipy
from discord import User
from googleapiclient.discovery import build
from spotipy.oauth2 import SpotifyClientCredentials
from src.bot.__tokens__ import __tokens__
from src.music.song import Song

youtube = build('youtube', 'v3', developerKey=__tokens__['google'])
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    __tokens__['spotify_client'], __tokens__['spotify']))


def get_songs(requester: User, query: str) -> list[Song]:
    # Youtube
    if query.find('youtube') != -1:
        # Playlist
        if query.find('list=') != -1:
            id = query[query.find('list=')+5:]
            if id.find('&') != -1:
                id = id[:id.find('&')]
            return get_youtube_playlist(requester, id)
        # Video
        id = query[query.find('watch?v=')+8:]
        if id.find('&') != -1:
            id = id[:id.find('&')]
        return get_youtube_video(requester, [id])
    # Spotify
    if query.find('spotify') != -1:
        # Playlist
        if query.find('playlist/') != -1:
            return getSpotifyPlaylist(requester, query[query.find('playlist/')+9:])
        # Video
        return getSpotifyTrack(requester, query[query.find('track/')+6:])
    # Youtube Search
    return search_youtube_video(requester, query)


def get_youtube_playlist(requester: User, id: str) -> list[Song]:
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
            playlistId=id
        )
        response = request.execute()

        if response['items']:
            for video in response['items'][:-1]:
                if video['snippet']['thumbnails']:
                    video_ids.append(video['contentDetails']['videoId'])
        playlist += get_youtube_video(requester, video_ids)

    return playlist


def get_youtube_video(requester: User, ids: list) -> list[Song]:
    videos = []
    if ids:
        id_string = ''
        for id in ids[:-1]:
            id_string += id + ','
        id_string += ids[-1]

        request = youtube.videos().list(
            part='snippet,contentDetails',
            id=id_string
        )
        response = request.execute()
        for video in response['items']:
            videos.append(Song(requester, video))

    return videos


def search_youtube_video(requester: User, query: str, max_results: int = 1) -> list[Song]:
    ids = []
    if query:
        request = youtube.search().list(
            part='snippet',
            maxResults=max_results,
            q=query
        )
        response = request.execute()

        for video in response['items']:
            if video['snippet']['thumbnails']:
                ids.append(video['id']['videoId'])
        return get_youtube_video(requester, ids)

    return []


def getSpotifyPlaylist(requester: User, id: str) -> list[Song]:
    track_names = []
    for meta in sp.playlist(id)['tracks']['items']:
        track_names.append(f'{meta["name"]} {meta["album"]["artists"][0]["name"]}')
    print(track_names)
    return []


def getSpotifyTrack(requester: User, id: str) -> list[Song]:
    meta = sp.track(id)
    trackName = f'{meta["name"]} {meta["album"]["artists"][0]["name"]}'
    return search_youtube_video(requester, trackName)
