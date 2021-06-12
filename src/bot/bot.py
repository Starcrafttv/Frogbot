import logging
import sqlite3
import zipfile
from datetime import datetime
from time import time

import discord
from discord import Activity, ActivityType, Game, Intents, Streaming
from discord.ext import commands, tasks
from src.bot.__tokens__ import __tokens__
from src.cogs.__cogs__ import __cogs__


class Bot(commands.Bot):
    def __init__(self):
        self.start_time = time()
        self.date = str(datetime.utcnow().date())
        self.description = 'a bot'
        self.loaded_cogs = []
        self.logo_url = 'https://i.ibb.co/NK4tkyf/Frog-Logonew.png'
        self.mainGuildId = 809129332684750889
        # dm system config
        self.supportCategoryId = 809130126410776576
        self.supportLogChannelId = 809130190507999244
        self.supportRoleId = 809129502248271922
        # Recorder dicts
        self.usersAfk = {}
        self.usersActive = {}
        # Connect to the database
        self.database_location = 'src/data/database.db'
        self.conn = sqlite3.connect(self.database_location)
        self.c = self.conn.cursor()
        # Create Logger
        self.logger = logging.getLogger('bot')
        self.logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler('src/data/bot.log')
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

    def _start(self):
        self.run(__tokens__['bot'])

    def _get_prefix(self, _, message: discord.Message):
        if message.guild:
            self.c.execute(f"SELECT Prefix FROM guilds WHERE GuildID = '{message.guild.id}'")
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

    def loadCog(self, cog):
        try:
            mod = __import__(f'src.cogs.{cog.lower()}', fromlist=[cog.lower().capitalize()])
            _class = getattr(mod, cog.capitalize())
            self.add_cog(_class(self))
            self.loaded_cogs.append(cog.lower())
        except Exception as e:
            return e
        return

    def removeCog(self, cog):
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
                zip_archive = zipfile.ZipFile(f'src/data/backup/db_{self.date}.zip', 'w')
                zip_archive.write('src/data/database.db', compress_type=zipfile.ZIP_DEFLATED)
                zip_archive.write('src/data/bot.log', compress_type=zipfile.ZIP_DEFLATED)
                zip_archive.close()
                self.logger.info('Backup created')
            except Exception as e:
                self.logger.exception(f'update_date - zip - {e}')

            self.date = str(datetime.utcnow().date())
            self.logger.info('Successfully changed date.')
            self.loadNew()
            self.logger.info('Reset of active and afk user')
