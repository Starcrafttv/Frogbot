import logging
import zipfile
from datetime import datetime
from time import time

import data.config as config
import requests
from discord import Activity, ActivityType, Game, Intents, Message, Streaming
from discord.ext import commands, tasks
from src.bot.__tokens__ import __tokens__
from src.cogs.__cogs__ import __cogs__


class Bot(commands.Bot):
    def __init__(self):
        self.header = {'token': __tokens__['frogbot_api']}
        self.base_api_url = config.base_api_url
        self.start_time = time()
        self.date = str(datetime.utcnow().date())
        self.description: str = config.description
        self.loaded_cogs: list[str] = []
        self.logo_url: str = config.logo_url
        self.main_guild_id = config.main_guild_id
        self.command_counter = 0
        self.open_searches = {}
        # dm system config
        self.support_category_id: int = config.support_category_id
        self.support_log_channel_id: int = config.support_log_channel_id
        self.support_role_id: int = config.support_role_id
        # Create Logger
        self.logger = logging.getLogger('bot')
        self.logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler(config.logging_file_location)
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        # add the handlers to logger
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)
        # Music
        self.voice_states = {}

        super().__init__(intents=Intents.all(), command_prefix=self._get_prefix,  description=self.description, case_insensitive=True)
        self.remove_command('help')

        self.date_loop.start()
        self.save_stats.start()

    def _start(self):
        self.run(__tokens__['bot'])

    def _get_prefix(self, _, message: Message):
        if message.guild:
            response = requests.get(f'{self.base_api_url}discord/guild/',
                                    params={'id': message.guild.id}, headers=self.header).json()
            if response.get('items'):
                return response['items'][0]['prefix']
        return '!'

    async def on_ready(self):
        await self.setStatus('s', 'with frogs')
        for extension in __cogs__:
            try:
                await self.loadCog(extension)
            except Exception as e:
                print(e)
        print(f'\n   Frogbot:\n'
              f'┌────────────────────────────────────────────────\n'
              f'│  Startup in {round(time() - self.start_time, 3)} seconds\n'
              f'│  {datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S")}\n'
              f'├────────────────────────────────────────────────\n'
              f'│  Version 1.0.0\n'
              f'│  Created by Niklas Mohler\n'
              f'│  Github https://github.com/Starcrafttv/Frogbot\n'
              f'├────────────────────────────────────────────────\n'
              f'│  LOGGED IN AS\n'
              f'│  Username: \'{self.user.name}#{self.user.discriminator}\'\n'
              f'│  ID: \'{self.user.id}\'\n'
              f'└────────────────────────────────────────────────\n')
        self.logger.info(
            f'Started {self.user.name}#{self.user.discriminator}, ID = {self.user.id} in {round(time() - self.start_time, 3)} seconds')

    async def setStatus(self, _type: str, message: str):
        if _type == 'w':
            await self.change_presence(activity=Activity(type=ActivityType.watching, name=message))
        elif _type == 'l':
            await self.change_presence(activity=Activity(type=ActivityType.listening, name=message))
        elif _type == 'p':
            await self.change_presence(activity=Game(name=message))
        elif _type == 's':
            await self.change_presence(activity=Streaming(name=message, url='http://www.twitch.tv/frogbot__'))

    async def loadCog(self, cog: str):
        try:
            mod = __import__(f'src.cogs.{cog.lower()}', fromlist=[cog.lower().capitalize()])
            _class = getattr(mod, cog.capitalize())
            self.add_cog(_class(self))
            self.loaded_cogs.append(cog.lower())
        except Exception as e:
            print(cog, e)
            return e
        return

    async def removeCog(self, cog: str):
        try:
            self.remove_cog(cog.lower().capitalize())
            self.loaded_cogs.remove(cog.lower())
        except Exception as e:
            return e
        return

    @tasks.loop(minutes=10)
    async def date_loop(self):
        # Backup
        if self.date == str(datetime.utcnow().date()):
            return

        await self.frogbot_entry()
        await self.create_backup()

        self.date = str(datetime.utcnow().date())
        self.logger.info('Successfully changed date.')

    async def create_backup(self):
        zip_archive = zipfile.ZipFile(f'data/backup/db_{self.date}.zip', 'w')
        zip_archive.write('data/bot.log', compress_type=zipfile.ZIP_DEFLATED)
        zip_archive.close()
        self.logger.info('Backup created')

    async def frogbot_entry(self):
        request = {
            'date': self.date,
            'guilds': len(self.guilds),
            'commandsUsed': self.command_counter
        }
        requests.put(f'{self.base_api_url}frogbot/entry/', params=request, headers=self.header)
        self.command_counter = 0

    async def user_active(self, user_id, channel_id, guild_id):
        requests.put(f'{self.base_api_url}discord/active/',
                     params={'userId': user_id,
                             'channelId': channel_id,
                             'guildId': guild_id},
                     headers=self.header)

    async def user_afk(self, user_id, channel_id, guild_id):
        requests.put(f'{self.base_api_url}discord/afk/',
                     params={'userId': user_id,
                             'channelId': channel_id,
                             'guildId': guild_id},
                     headers=self.header)

    @tasks.loop(minutes=10)
    async def save_stats(self):
        requests.put(f'{self.base_api_url}discord/save/stats', headers=self.header)

        for guild in self.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if not member.bot:
                        if member.voice.afk or member.voice.deaf or member.voice.mute or member.voice.self_deaf or member.voice.self_mute:
                            await self.user_afk(member.id, channel.id, guild.id)
                        else:
                            await self.user_active(member.id, channel.id, guild.id)
