import logging
import sqlite3
import zipfile
from datetime import datetime
from time import time

import data.config as config
from discord import Activity, ActivityType, Game, Intents, Message, Streaming
from discord.ext import commands, tasks
from src.bot.__tokens__ import __tokens__
from src.cogs.__cogs__ import __cogs__
from src.stats.entry import Active, Afk


class Bot(commands.Bot):
    def __init__(self):
        self.start_time = time()
        self.date = str(datetime.utcnow().date())
        self.description = config.description
        self.loaded_cogs = []
        self.logo_url = config.logo_url
        self.mainGuildId = config.mainGuildId
        # dm system config
        self.support_category_id = config.support_category_id
        self.support_log_channel_id = config.support_log_channel_id
        self.support_role_id = config.support_role_id
        # Recorder dicts
        self.users_afk = {}
        self.users_active = {}
        # Connect to the database
        self.database_location = config.database_location
        self.conn = sqlite3.connect(self.database_location)
        self.c = self.conn.cursor()
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
        self.save_entry_loop.start()

    def _start(self):
        self.run(__tokens__['bot'])

    def _get_prefix(self, _, message: Message):
        if message.guild:
            self.c.execute(f"SELECT Prefix FROM guilds WHERE GuildID = {message.guild.id}")
            prefix = self.c.fetchone()
            if prefix:
                return prefix[0]
        return '!'

    async def on_ready(self):
        await self.setStatus('s', 'with frogs')
        for extension in __cogs__:
            try:
                self.loadCog(extension)
            except Exception as e:
                print(e)
        print(f'{self.user}, {round(time() - self.start_time, 3)}, is ready to go')
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

    def loadCog(self, cog: str):
        try:
            mod = __import__(f'src.cogs.{cog.lower()}', fromlist=[cog.lower().capitalize()])
            _class = getattr(mod, cog.capitalize())
            self.add_cog(_class(self))
            self.loaded_cogs.append(cog.lower())
        except Exception as e:
            print(cog, e)
            return e
        return

    def removeCog(self, cog: str):
        try:
            self.remove_cog(cog.lower().capitalize())
            self.loaded_cogs.remove(cog.lower())
        except Exception as e:
            return e
        return

    @tasks.loop(minutes=10)
    async def date_loop(self):
        # Backup
        if self.date != str(datetime.utcnow().date()):
            try:
                with self.conn:
                    self.c.execute(
                        f"INSERT INTO botStats (Date, Guilds, CommandsUsed) VALUES ('{str(self.date)}', {len(self.guilds)}, {self.commandCounter})")
            except Exception as e:
                self.logger.exception(f'update_date - {e}')
            self.commandCounter = 0

            try:
                zip_archive = zipfile.ZipFile(f'data/backup/db_{self.date}.zip', 'w')
                zip_archive.write('data/database.db', compress_type=zipfile.ZIP_DEFLATED)
                zip_archive.write('data/bot.log', compress_type=zipfile.ZIP_DEFLATED)
                zip_archive.close()
                self.logger.info('Backup created')
            except Exception as e:
                self.logger.exception(f'update_date - zip - {e}')

            self.date = str(datetime.utcnow().date())
            self.logger.info('Successfully changed date.')
            self.loadNew()
            self.logger.info('Reset of active and afk user')

    @tasks.loop(minutes=10)
    async def save_entry_loop(self):
        for user in self.users_active.values():
            user.save(self.conn, self.c)
        for user in self.users_afk.values():
            user.save(self.conn, self.c)
        self.users_active = {}
        self.users_afk = {}

        for guild in self.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if (member.voice.afk or member.voice.deaf or member.voice.mute or member.voice.self_deaf or member.voice.self_mute) and not member.id in self.users_afk:
                        self.users_afk[member.id] = Afk(member.id, channel.id, guild.id)
                    elif not member.id in self.users_active:
                        self.users_active[member.id] = Active(member.id, channel.id, guild.id)
