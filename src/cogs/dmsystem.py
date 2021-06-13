from discord import Message
from discord.ext import commands
from src.bot.bot import Bot


class Dmsystem(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        if not message.guild and not message.author.bot and message.content[0] != '!':
            self.bot.c.execute(f"SELECT ChannelID FROM dms WHERE UserID = {message.author.id}")
            channelID = self.bot.c.fetchone()
            if not channelID:
                channel = await self.bot.fetch_channel(self.bot.support_log_channel_id)
                newChannel = await channel.guild.create_text_channel(f'ticket-{message.author.name}-{message.author.id}')
                category = self.bot.get_channel(self.bot.support_category_id)
                await newChannel.edit(category=category)
                await newChannel.set_permissions(channel.guild.default_role,
                                                 read_messages=False,
                                                 send_messages=False)
                await newChannel.set_permissions(channel.guild.get_role(self.bot.support_role_id),
                                                 send_messages=True,
                                                 read_messages=True,
                                                 embed_links=True,
                                                 attach_files=True,
                                                 read_message_history=True,
                                                 add_reactions=True)
                await newChannel.send(f"{message.author.name}: {message.content}")
                with self.bot.conn:
                    self.bot.c.execute(
                        f"INSERT INTO dms (UserID, ChannelID) VALUES ({message.author.id}, {newChannel.id})")
                await message.reply("Thank you for your message! Our mod team will reply to you as soon as possible.", mention_author=False)
            else:
                channel = await self.bot.fetch_channel(channelID[0])
                await channel.send(f"{message.author.name}: {message.content}")
            return
        self.bot.c.execute(f"SELECT UserID FROM dms WHERE ChannelID = {message.channel.id}")
        userID = self.bot.c.fetchone()
        self.bot.c.execute(f"SELECT Prefix FROM guilds WHERE GuildID = {self.bot.mainGuildId}")
        prefix = self.bot.c.fetchone()[0]
        if userID and message.content[0] != prefix:
            await self.bot.get_user(int(userID[0])).send(message.content)
            await message.add_reaction("✅")

    @commands.command(name='close', hidden=True)
    @commands.is_owner()
    async def close(self, ctx: commands.Context):
        self.bot.c.execute(f"SELECT UserID FROM dms WHERE ChannelID = {ctx.channel.id}")
        userID = self.bot.c.fetchone()
        if userID:
            with self.bot.conn:
                self.bot.c.execute(f"DELETE FROM dms WHERE UserID = {userID[0]}")
            log = f"User-ID:'{userID[0]}'\n"
            messages = await ctx.channel.history(limit=200).flatten()
            for message in reversed(messages):
                log = f"{log}{message.created_at.strftime('%d.%m.%y %H:%M')} | {message.author.name}: {message.content}\n"
            log = f"```{log}```"
            logChannel = ctx.channel.guild.get_channel(self.bot.support_log_channel_id)
            await logChannel.send(log)
            await ctx.channel.delete()

    @commands.command(name='open Dms', aliases=['od'], hidden=True)
    @commands.is_owner()
    async def openDms(self, ctx: commands.Context):
        self.bot.c.execute(f"SELECT UserID, ChannelID FROM dms")
        message = ""
        for dm in self.bot.c.fetchall():
            message = f"{message}User ID:{dm[0]}, Channel ID:{dm[1]}\n"
        if not message:
            message = "No open tickets"
        await ctx.send(f"```{message}```")
