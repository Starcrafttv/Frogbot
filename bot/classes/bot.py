import logging
import os
import shutil
import sqlite3
import zipfile
from datetime import datetime
from time import time

from discord import Activity, ActivityType, Game, Intents, Streaming
from discord.ext import commands, tasks

from bot.__tokens__ import __tokens__
from bot.classes.entry import Active, Afk


class Bot():
    def __init__(self):
        # Create a discord client
        self.client = commands.Bot(intents=Intents.all(), command_prefix=self.getPrefix, case_insensitive=True)
        self.client.remove_command('help')
        # Set important variables
        if os.path.exists('bot/data/temp'):
            shutil.rmtree('bot/data/temp')
        os.mkdir('bot/data/temp')
        self.startTime = time()
        self.voiceClients = {}
        self.loadedCogs = []
        self.logoUrl = 'https://i.ibb.co/NK4tkyf/Frog-Logonew.png'
        self.usersActive = {}
        self.usersAfk = {}
        self.commandCounter = 0
        self.date = str(datetime.utcnow().date())
        self.mainGuildId = 809129332684750889
        self.supportCategoryId = 809130126410776576
        self.supportLogChannelId = 809130190507999244
        self.supportRoleId = 809129502248271922
        # Create Logger
        self.logger = logging.getLogger('bot')
        self.logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler('bot/data/bot.log')
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
        # Connect to the database
        self.conn = sqlite3.connect('bot/data/database.db')
        self.c = self.conn.cursor()
        self.Musicloop.start()
        self.DateLoop.start()
        self.statsLoop.start()

    def getPrefix(self, bot, message):
        if message.guild:
            self.c.execute(f"SELECT Prefix FROM guilds WHERE GuildID = '{message.guild.id}'")
            prefix = self.c.fetchone()
            if prefix:
                return prefix[0]
        return '!'

    async def setStatus(self, _type: str, message: str):
        if _type == 'w':
            await self.client.change_presence(activity=Activity(type=ActivityType.watching, name=message))
        elif _type == 'l':
            await self.client.change_presence(activity=Activity(type=ActivityType.listening, name=message))
        elif _type == 'p':
            await self.client.change_presence(activity=Game(name=message))
        elif _type == 's':
            await self.client.change_presence(activity=Streaming(name=message, url='http://www.twitch.tv/frogbot__'))

    def start(self):
        self.client.run(__tokens__['bot'])

    def loadCog(self, cog):
        try:
            mod = __import__(f'bot.cogs.{cog.lower()}', fromlist=[cog.lower().capitalize()])
            _class = getattr(mod, cog.capitalize())
            self.client.add_cog(_class(self))
            self.loadedCogs.append(cog.lower())
        except Exception as e:
            return e
        return

    def removeCog(self, cog):
        try:
            self.client.remove_cog(cog.lower().capitalize())
            self.loadedCogs.remove(cog.lower())
        except Exception as e:
            return e
        return

    def loadNew(self):
        self.usersActive = {}
        self.usersAfk = {}
        for guild in self.client.guilds:
            self.c.execute(f"SELECT GuildID FROM guilds WHERE GuildID = '{guild.id}'")
            if not self.c.fetchone():
                with self.conn:
                    self.c.execute(f"INSERT INTO guilds (GuildID) VALUES ('{guild.id}')")
            for channel in guild.voice_channels:
                for member in channel.members:
                    if (member.voice.afk or member.voice.deaf or member.voice.mute or member.voice.self_deaf or member.voice.self_mute) and not member.id in self.usersAfk:
                        self.usersAfk[member.id] = Afk(member.id, channel.id, guild.id)
                    elif not member.id in self.usersActive:
                        self.usersActive[member.id] = Active(member.id, channel.id, guild.id)
        for user in self.client.users:
            self.c.execute(f"SELECT UserID FROM users WHERE UserID = '{user.id}'")
            if not self.c.fetchone():
                with self.conn:
                    self.c.execute(f"INSERT INTO users (UserID) VALUES ('{user.id}')")

    @tasks.loop(seconds=4)
    async def Musicloop(self):
        # Music
        try:
            for voiceClient in self.voiceClients.values():
                if not voiceClient.allInfos:
                    for song in voiceClient.queue:
                        if not song.title:
                            if not song.loadInfo():
                                voiceClient.queue.remove(song)
                            break
                    else:
                        voiceClient.allInfos = True

            for voiceClient in self.voiceClients.values():
                if voiceClient.following:
                    for member in voiceClient.voiceClient.channel.members:
                        if member.id == voiceClient.following:
                            for activity in member.activities:
                                if activity.name == "Spotify":
                                    requester = f'{member.name}#{member.discriminator}'
                                    query = f'{activity.title} {activity.artist}'
                                    if query != voiceClient.followingQ:
                                        voiceClient.followingQ = query
                                        voiceClient.loadSongs(query, requester, True)
                                    break
                                else:
                                    voiceClient.following = None
                            break
                    else:
                        voiceClient.following = None

                if voiceClient.voiceClient.is_connected() == False:
                    if voiceClient.reactMessageId:
                        message = await self.client.get_channel(voiceClient.reactMessageChannelId).fetch_message(voiceClient.reactMessageId)
                        await message.clear_reactions()
                    print(voiceClient.timeout)
                    print("bot.py - l. 158 - pop - not is_connected")
                    self.voiceClients.pop(voiceClient.guildId)
                elif voiceClient.timeout >= voiceClient.timeoutMax:
                    if voiceClient.reactMessageId:
                        message = await self.client.get_channel(voiceClient.reactMessageChannelId).fetch_message(voiceClient.reactMessageId)
                        await message.clear_reactions()
                    await voiceClient.voiceClient.disconnect()
                    print(voiceClient.timeout)
                    print("bot.py - l. 166 - pop - timeout")
                    self.voiceClients.pop(voiceClient.guildId)
                elif voiceClient.voiceClient.is_playing() == False and voiceClient.queue == []:
                    voiceClient.timeout += 4
                elif voiceClient.voiceClient.is_playing() == False and voiceClient.playing and (voiceClient.queue or (voiceClient.loopSong and voiceClient.currentSong)):
                    voiceClient.nextTrack()
                elif voiceClient.voiceClient.is_playing():
                    for member in voiceClient.voiceClient.channel.members:
                        if not member.bot:
                            voiceClient.timeout = 0
                            break
                    else:
                        voiceClient.timeout += 5
        except Exception as e:
            print(e)

    @tasks.loop(minutes=5)
    async def DateLoop(self):
        # Backup
        if self.date != str(datetime.utcnow().date()):
            try:
                with self.conn:
                    self.c.execute(
                        f"INSERT INTO botStats (Date, Guilds, CommandsUsed) VALUES ('{str(self.date)}', {len(self.client.guilds)}, {self.commandCounter})")
            except Exception as e:
                self.logger.exception(f'update_date - {e}')
            self.commandCounter = 0

            try:
                zip_archive = zipfile.ZipFile(f'bot/data/backup/db_{self.date}.zip', 'w')
                zip_archive.write('bot/data/database.db', compress_type=zipfile.ZIP_DEFLATED)
                zip_archive.write('bot/data/bot.log', compress_type=zipfile.ZIP_DEFLATED)
                zip_archive.close()
                self.logger.info('Backup created')
            except Exception as e:
                self.logger.exception(f'update_date - zip - {e}')

            self.date = str(datetime.utcnow().date())
            self.logger.info('Successfully changed date.')
            self.loadNew()
            self.logger.info('Reset of active and afk user')

    @tasks.loop(minutes=5)
    async def statsLoop(self):
        for user_id in self.usersActive:
            self.usersActive[user_id].save(self.conn, self.c)
            self.usersActive[user_id].setStart()
        for user_id in self.usersAfk:
            self.usersAfk[user_id].save(self.conn, self.c)
            self.usersAfk[user_id].setStart()
