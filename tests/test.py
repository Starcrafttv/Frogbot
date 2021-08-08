import re
import urllib.request

import requests
from emoji import demojize


def search_youtube_video(query: str, max_results: int = 1):
    url = demojize(f'https://www.youtube.com/results?search_query={query.replace(" ", "+")}&sp=EgIQAQ%253D%253D')
    print(url)
    request = requests.get(url)
    print(re.findall(r'watch\?v=(\S{11})', request.text)[:max_results])
    # return re.findall(r'watch\?v=(\S{11})', request.read().decode())[:max_results]


search_youtube_video('feeling like an astro', 5)
