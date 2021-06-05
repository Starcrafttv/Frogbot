from time import time

from googleapiclient.discovery import build

from bot.__tokens__ import __tokens__
from bot.classes.song import Song

youtube = build('youtube', 'v3', developerKey=__tokens__['google'])

"""
    query = "Running with the speed of light"
    length = 1

    songs = []
    request = youtube.search().list(
        part='snippet',
        maxResults=length,
        q=query
    )
    response = request.execute()


    for song in response["items"]:
        print(f"ID: {song['id']['videoId']}")
        print(f"Title: {song['snippet']['title']}")
        print(f"Channel: {song['snippet']['channelTitle']}")
        print(f"Thumbnail url: {song['snippet']['thumbnails']['default']['url']}")
"""


def getPlaylist(playlistId, requester):
    global maxres, standard, high, medium, default
    songs = []
    response = {'nextPageToken': None}
    # Go through each playlist page and extract all videos in it
    while True:
        if 'nextPageToken' not in response.keys():
            break
        request = youtube.playlistItems().list(
            part='contentDetails, snippet',
            maxResults=50,
            pageToken=response['nextPageToken'],
            playlistId=playlistId
        )
        response = request.execute()
        if response['items']:
            for video in response['items'][:-1]:
                if video['snippet']['thumbnails']:
                    songs.append(Song(video['contentDetails']['videoId'], requester, video))
    return songs


pl = "PLOzDu-MXXLliO9fBNZOQTBDddoA3FzZUo"
botpl = "PLjqIl05HD0UXfubD0Oa6mVAkTKtK_cQe4"
pop = "PL4o29bINVT4EG_y-k5jGoOu3-Am8Nvi10"
requester = "starcraft#3249"
start = time()
songs = getPlaylist(pop, requester)
print(f"Time: {round(time()-start, 2)}")

print(songs[10].title)
print(len(songs))
