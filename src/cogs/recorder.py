from discord import Guild, Member, Message, VoiceState
from discord.ext import commands
from src.bot.bot import Bot
from src.stats.entry import Active, Afk, saveMessage


class Recorder(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        for guild in self.bot.guilds:
            self.bot.c.execute(f"SELECT GuildID FROM guilds WHERE GuildID = {guild.id}")
            if not self.bot.c.fetchone():
                with self.bot.conn:
                    self.bot.c.execute(f"INSERT INTO guilds (GuildID) VALUES ({guild.id})")
            for channel in guild.voice_channels:
                for member in channel.members:
                    if (member.voice.afk or member.voice.deaf or member.voice.mute or member.voice.self_deaf or member.voice.self_mute) and not member.id in self.bot.users_afk:
                        self.bot.users_afk[member.id] = Afk(member.id, channel.id, guild.id)
                    elif not member.id in self.bot.users_active:
                        self.bot.users_active[member.id] = Active(member.id, channel.id, guild.id)
        for user in self.bot.users:
            self.bot.c.execute(f"SELECT UserID FROM users WHERE UserID = {user.id}")
            if not self.bot.c.fetchone():
                with self.bot.conn:
                    self.bot.c.execute(f"INSERT INTO users (UserID) VALUES ({user.id})")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if (after.afk or after.deaf or after.mute or after.self_deaf or after.self_mute) and after.channel:
            if not member.id in self.bot.users_afk:
                self.bot.users_afk[member.id] = Afk(member.id, after.channel.id, member.guild.id)
            if member.id in self.bot.users_active:
                self.bot.users_active[member.id].save(self.bot.conn, self.bot.c)
                self.bot.users_active.pop(member.id)
        elif after.channel:
            if not member.id in self.bot.users_active:
                self.bot.users_active[member.id] = Active(member.id, after.channel.id, member.guild.id)
            if member.id in self.bot.users_afk:
                self.bot.users_afk[member.id].save(self.bot.conn, self.bot.c)
                self.bot.users_afk.pop(member.id)
        elif not after.channel:
            if member.id in self.bot.users_afk:
                self.bot.users_afk[member.id].save(self.bot.conn, self.bot.c)
                self.bot.users_afk.pop(member.id)
            elif member.id in self.bot.users_active:
                self.bot.users_active[member.id].save(self.bot.conn, self.bot.c)
                self.bot.users_active.pop(member.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        # add the user to the data base if he is new
        self.bot.c.execute(f"SELECT UserID FROM users WHERE UserID = {member.id}")
        if not self.bot.c.fetchone():
            with self.bot.conn:
                self.bot.c.execute(f"INSERT INTO users (UserID) VALUES ({member.id})")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        # add the guild to the database if it is new
        self.bot.logger.info(f'NEW GUILD - {guild.name} - {guild.id} - Members: {guild.member_count}')
        self.bot.c.execute(f"SELECT GuildID FROM guilds WHERE GuildID = {guild.id}")
        if not self.bot.c.fetchone():
            with self.bot.conn:
                self.bot.c.execute(f"INSERT INTO guilds (GuildID) VALUES ({guild.id})")
        # Check for new users
        for member in guild.members:
            self.bot.c.execute(f"SELECT UserID FROM users WHERE UserID = {member.id}")
            if not self.bot.c.fetchone():
                with self.bot.conn:
                    self.bot.c.execute(f"INSERT INTO users (UserID) VALUES ({member.id})")

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        saveMessage(message.author.id, message.channel.id, message.guild, self.bot.conn, self.bot.c)
