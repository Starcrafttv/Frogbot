from datetime import datetime, timedelta

from discord import Colour, Embed, Message
from discord.ext import commands
from src.bot.bot import Bot


class General(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name='help')
    async def help(self, ctx: commands.Context, arg: str = ''):
        if ctx.author.bot:
            return

        if ctx.guild:
            self.bot.c.execute(f"SELECT Prefix FROM guilds WHERE GuildID = {ctx.guild.id}")
            prefix = self.bot.c.fetchone()[0]
        else:
            prefix = '!'

        embed = Embed(title=':book: A list of all commands:',
                      description='‎‎\u200b',
                      inline=False,
                      colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        embed.add_field(name=f'**`{prefix}music`**',
                        value='Shows all available music commands',
                        inline=False)
        embed.add_field(name=f'**`{prefix}stats <days> <plot> <raw> <total>`**',
                        value='Displays your stats over the selected last days.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}leaderboard <positions> <plot> <last_days=days> <active/afk>`**',
                        value='Creates a leaderboard for the current discord server.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}average <days>`**',
                        value='Calculates your average stats over the last days.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}settings`**',
                        value='Options to customize the bot.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}timezone <your_timezone>`**',
                        value='Necessary to accurately display your stats.',
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='music')
    async def music(self, ctx: commands.Context, arg: str = ''):
        if ctx.author.bot and not ctx.guild:
            return

        self.bot.c.execute(f"SELECT Prefix FROM guilds WHERE GuildID = {ctx.guild.id}")
        prefix = self.bot.c.fetchone()[0]

        embed = Embed(title=':book: A list of all music commands:',
                      description='‎‎\u200b',
                      inline=False,
                      colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        embed.add_field(name=f'**`{prefix}join/leave`**',
                        value='Joins/leaves your channel',
                        inline=False)
        embed.add_field(name=f'**`{prefix}play <song>`**',
                        value='Plays a song with the given name or url.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}skip`**',
                        value='Skips the current song',
                        inline=False)
        embed.add_field(name=f'**`{prefix}queue <page>`**',
                        value='Shows the a page of the queue.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}shuffle`**',
                        value='Shuffles the entire queue.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}clear`**',
                        value='Clears the whole queue.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}move <old_position> <new_position>`**',
                        value='Moves a certain song to a chosen position in the queue.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}remove <song_position>`**',
                        value='Removes a certain entry from the queue.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}loopsong/loopqueue`**',
                        value='Toggles looping for the current Song/the whole queue.',
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='invite', aliases=['inv'])
    async def invite(self, ctx: commands.Context, *, args: str = ''):
        embed = Embed(
            title='\u200b',
            description=f'[Invite me](https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=37088320)',
            inline=False, colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        await ctx.send(embed=embed)

    @commands.command(name='timezone', aliases=['tz'])
    async def timezone(self, ctx: commands.Context, *, timezone=None):
        if timezone == None:
            self.bot.c.execute(f"SELECT Timezone FROM users WHERE UserID = {ctx.author.id}")
            await ctx.send(f":clock9: Your current timezone should be {(datetime.utcnow() + timedelta(hours=self.bot.c.fetchone()[0])).strftime('%H:%M')} o'clock for you.")
            return
        try:
            timezone = int(timezone)
            if timezone < -12 or timezone > 12:
                await ctx.send('Your timezone must be between -12 and 12')
                return
            else:
                with self.bot.conn:
                    self.bot.c.execute(f"UPDATE users SET Timezone = {timezone} WHERE UserID = {ctx.author.id}")
                await ctx.send(f":clock9: Successfully updated your timezone. It should be {(datetime.utcnow() + timedelta(hours=timezone)).strftime('%H:%M')} o'clock for you.")
                return
        except ValueError:
            return

    @commands.command(name='settings', aliases=['setting', 'seting'])
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def settings(self, ctx: commands.Context, *, args: str = ''):
        args = [arg.lower().replace("'", '`') for arg in args.split(' ')]
        if args[0] in ['prefix']:
            if len(args) > 1 and args[1] and len(args[1]) < 6:
                with self.bot.conn:
                    self.bot.c.execute(f"UPDATE guilds SET Prefix = '{args[1]}' WHERE GuildID = {ctx.guild.id}")
                    await ctx.send(f":white_check_mark: Prefix set to '**`{args[1]}`**' ")
            else:
                await ctx.send("The prefix can't be longer then five characters.")
        elif args[0] in ['volume', 'vol']:
            if len(args) > 1 and args[1]:
                try:
                    volume = int(args[1])
                    if 0 <= volume <= 100:
                        with self.bot.conn:
                            self.bot.c.execute(f"UPDATE guilds SET Volume = {volume} WHERE GuildID = {ctx.guild.id}")
                        if ctx.guild.id in self.bot.voice_states:
                            self.bot.voice_states[ctx.guild.id]._volume = volume/100
                        await ctx.message.add_reaction('🐸')
                    else:
                        await ctx.send('The volume must be between 0 and 100')
                except Exception:
                    await ctx.send('The volume must be a number')
        elif args[0] in ['timeout']:
            if len(args) > 1 and args[1]:
                try:
                    timeout = int(args[1])
                    if 0 <= timeout <= 6000:
                        with self.bot.conn:
                            self.bot.c.execute(
                                f"UPDATE guilds SET Timeout = {timeout} WHERE GuildID = {ctx.guild.id}")
                        if ctx.guild.id in self.bot.voice_states:
                            self.bot.voice_states[ctx.guild.id].timeout = timeout
                        await ctx.message.add_reaction('🐸')
                    else:
                        await ctx.send('The timeout must be between 0 and 6000')
                except Exception:
                    await ctx.send('The timeout must be a number')
        elif args[0] in ['musicrole', 'mr']:
            if len(args) > 1 and args[1]:
                try:
                    musicrole = int(args[1])
                    with self.bot.conn:
                        self.bot.c.execute(
                            f"UPDATE guilds SET ReqRole = {musicrole} WHERE GuildID = {ctx.guild.id}")
                    await ctx.message.add_reaction('🐸')
                except Exception:
                    await ctx.send('The music role must be a number')
        elif args[0] in ['musicchannel', 'mc']:
            if len(args) > 1 and args[1]:
                try:
                    musicChannelId = int(args[1])
                    with self.bot.conn:
                        self.bot.c.execute(
                            f"UPDATE guilds SET MusicChannelId = {musicChannelId} WHERE GuildID = {ctx.guild.id}")
                    if ctx.guild.id in self.bot.voice_states:
                        self.bot.voice_states[ctx.guild.id].music_channel_id = musicChannelId
                    await ctx.message.add_reaction('🐸')
                except Exception:
                    await ctx.send('The music channel must be a number')
        elif args[0] in ['reset']:
            if len(args) > 1 and args[1] == 'true':
                with self.bot.conn:
                    self.bot.c.execute(f"UPDATE guilds SET Prefix = '!' WHERE GuildID = {ctx.guild.id}")
                    self.bot.c.execute(f"UPDATE guilds SET Volume = 50 WHERE GuildID = {ctx.guild.id}")
                    self.bot.c.execute(f"UPDATE guilds SET MusicChannelId = 0 WHERE GuildID = {ctx.guild.id}")
                    self.bot.c.execute(f"UPDATE guilds SET Timeout = 300 WHERE GuildID = {ctx.guild.id}")
                    self.bot.c.execute(f"UPDATE guilds SET ReqRole = 0 WHERE GuildID = {ctx.guild.id}")
                if ctx.guild.id in self.bot.voice_states:
                    self.bot.voice_states[ctx.guild.id].music_channel_id = 0
                    self.bot.voice_states[ctx.guild.id]._volume = 0.5
                    self.bot.voice_states[ctx.guild.id].timeout = 300
                await ctx.send(f':white_check_mark: Reset all settings for this guild.')
            else:
                self.bot.c.execute(f"SELECT Prefix FROM guilds WHERE GuildID = {ctx.guild.id}")
                prefix = self.bot.c.fetchone()[0]
                embed = Embed(title='Reset',
                              description=f'Resets all settings for the bot in this guild.',
                              inline=False,
                              colour=Colour.blue())
                embed.set_thumbnail(url=self.bot.logo_url)
                embed.add_field(name='Command:',
                                value=f'**`{prefix}settings reset true`**',
                                inline=False)
                await ctx.send(embed=embed)
        else:
            self.bot.c.execute(f"SELECT Prefix FROM guilds WHERE GuildID = {ctx.guild.id}")
            prefix = self.bot.c.fetchone()[0]
            embed = Embed(title=':gear: Frogbot settings',
                          description='Use this command to customize this bot.',
                          inline=False,
                          colour=Colour.blue())
            embed.set_thumbnail(url=self.bot.logo_url)
            embed.add_field(name='Prefix:',
                            value=f'**`{prefix}settings prefix <prefix>`**')
            embed.add_field(name='Timeout:',
                            value=f'**`{prefix}settings timeout <timeout>`**')
            embed.add_field(name='Volume:',
                            value=f'**`{prefix}settings volume <volume>`**')
            embed.add_field(name='Music Channel:',
                            value=f'**`{prefix}settings musicchannel <music_channel_id>`**')
            embed.add_field(name='Music Role:',
                            value=f'**`{prefix}settings musicrole <music_role_id>`**')
            embed.add_field(name='Reset:',
                            value=f'**`{prefix}settings reset`**')
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if not message.author.bot and message.content.find(f'<@!{self.bot.user.id}>') != -1:
            if message.guild:
                self.bot.c.execute(f"SELECT Prefix FROM guilds WHERE GuildID = {message.guild.id}")
                await message.channel.send(f'My current prefix is **`{self.bot.c.fetchone()[0]}`**')
            else:
                await message.channel.send(f'My current prefix is **`!`**')
