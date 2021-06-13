# Frogbot

[![Python3](https://img.shields.io/badge/python-3.9-green.svg)](https://github.com/Starcrafttv/Frogbot)
[![Discord Server](https://img.shields.io/badge/Support-Discord%20Server-green.svg)](https://discord.gg/VUqdtHtHqcc)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
## General:
This Discord bot logs some interesting information about users in your guild. A user is considered as active if he is in a voice channel and not muted. If he is muted, he is considered as afk. The bot also counts how many messages a user sends per day. This bot encourages members to compare themselves with others and to be more active on the Discord server.

If you have any other trouble with the bot or ideas for improvement just direct message the bot and our mod team will respond as soon as possible.

You can invite the bot to your discord server [here](https://discord.com/oauth2/authorize?client_id=840862571102994452&scope=bot&permissions=8) or if you need additional support you can join this discord server [here](https://discord.gg/VUqdtHtHqc).

## Commands:

Command | Description | Example
--- | --- | ---
`!help <command>` | Returns a list of all commands. You can get more information about any command and its use by adding the command behind the help command | `!help stats` 
`!stats <days> <plot/raw> <total>` | Sends information about your active and afk times as well as you messages sent. You can get more days by adding any amount of days behind like this: `!stats 5`. You can also get it graphically by adding the word `plot` behind. If you add `raw` the bot will create a more detailed graphic about your online times. On default the bot only displays the stats for the guild you write the command in. To get your total stats add `total`. | `!stats 5 plot`
`!leaderboard <positions> <days=x> <plot>` | This returns a leaderboard for the top five active users on your server. You can get more or less positions by adding your wished positions behind. Again you can get it graphically displayed by adding `plot`. You can also add `days=5` to get a leaderboard for the last `5` days.| `!leaderboard 3 plot days=5`
`!compare <days> <user1> <user2>` | You can also compare two or more user with this command. You just need to add another persons username behind and the bot will create a graphic with you and the other user/s | `!compare user1 user2`
`!average <days>` | Returns your average stats. You can add any amount of days behind it. | `!average 7`
`!timezone <x>` | The bot needs this if you live in any other timezone then +0. Just add your timezone behind to make your stats more accurate. This can be adjusted later on. | `!timezone -6`
`!settings` | If you want to change the prefix for the bot in your server you need to be a administrator of the server to do so. If you don't know the current prefix just ping the bot and it will respond with its current prefix. | `!settings prefix ?`


## Graphics:

Example stats with the `plot` specification:
![example_stats](https://i.ibb.co/443JbVV/example-stats.png)

Example stats with the `raw` specification:
![example_raw_stats](https://i.ibb.co/CQLCY0K/example-raw-stats.png)

Example leaderboard with the `plot` specification:
![example_leaderboard](https://i.ibb.co/HVw22FM/example-leaderboard.png)

## About the code:
This bot is coded in python. The data is stored in a database with sqlite. Every type of command is separated in a different cog. If you want to run this bot you need a `__tokens__.py` file under `src/bot/`. This file should look like this:
```python
__tokens__ = {
    'bot': '',
    'google': '',
    'spotify': '',
    'spotify_client': '',
    'lol': ''
}
```
You can get all of these api keys for free.

I also did not upload the full database because it contains personal data of users. There is a `transfer.py` under `tests/` that creates a fresh database for you.The bot has a log file under `data/bot.log` and automatically creates backups under `data/backup/` with the data as the name.

I added some features only the owner of the bot can use. There also is a dm system that needs to be adjusted to your own server if you want to run the bot. With this users can dm the bot and you can answer them over a channel the bot created.

There are a lot of other features one can find in my code.

## List of requirements:
- `python`>= 3.8.5

- `discord.py`
- `matplotlib`
- `emoji` (used so matplotlib can work with emojis in usernames)
- `pynacl`
- `youtube_dl`
- `spotipy`
- `google-api-python-client`
- `google-auth-httplib2`
- `google-auth-oauthlib`
- `cassiopeia` (currently working on a new cog for League of Legends stats)


Please excuse any weird spelling or grammar, I am german...

Copyright © 2021 Niklas Mohler - All rights reserved

![Frogbot logo](https://i.ibb.co/NK4tkyf/Frog-Logonew.png)