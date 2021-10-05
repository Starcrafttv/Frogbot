from datetime import datetime, timedelta

import requests
from nextcord import ChannelType, Colour, Embed, Message
from nextcord.ext import commands
from src.bot.bot import Bot


class General(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name='help')
    async def help(self, ctx: commands.Context, arg: str = ''):
        if ctx.author.bot:
            return

        if ctx.guild:
            response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                    params={'id': ctx.guild.id}, headers=self.bot.header).json()
            prefix = response['items'][0]['prefix'] if response.get('items') else '!'
        else:
            prefix = '!'

        embed = Embed(title=':book: A list of all commands:',
                      description='‎‎\u200b',
                      colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        embed.add_field(name=f'**`{prefix}music`**',
                        value='Shows all available music commands',
                        inline=False)
        embed.add_field(name=f'**`{prefix}playlists`**',
                        value='Shows all available music commands',
                        inline=False)
        embed.add_field(name=f'**`{prefix}stats <days> <plot> <raw> <total>`**',
                        value='Displays your stats over the selected last days',
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
    async def music(self, ctx: commands.Context, *, arg: str = ''):
        if ctx.author.bot and not ctx.guild:
            return

        response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                params={'id': ctx.guild.id}, headers=self.bot.header).json()
        prefix = response['items'][0]['prefix'] if response.get('items') else '!'
        embed = Embed(title=':book: A list of all music commands:',
                      description='‎‎\u200b',
                      colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        embed.add_field(name=f'**`{prefix}join/leave`**',
                        value='Joins/leaves your channel',
                        inline=False)
        embed.add_field(name=f'**`{prefix}play <song>`**',
                        value='Plays a song with the given name or url (playskip or playtop work the same way).',
                        inline=False)
        embed.add_field(name=f'**`{prefix}find <song>`**',
                        value='Searches Youtube for a song and gives the top 5 results.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}skip`**',
                        value='Skips the current song',
                        inline=False)
        embed.add_field(name=f'**`{prefix}seek <hours:minutes:seconds>`**',
                        value='Skips to any position in the song.',
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

    @commands.command(name='playlists', aliases=['playlist'])
    async def playlists(self, ctx: commands.Context, *, arg: str = ''):
        if ctx.author.bot and not ctx.guild:
            return

        response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                params={'id': ctx.guild.id}, headers=self.bot.header).json()
        prefix = response['items'][0]['prefix'] if response.get('items') else '!'
        embed = Embed(title=':book: A list of all playlist commands:',
                      description='All playlists are user specific but can be added to guilds for other people to use.',
                      colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        embed.add_field(name=f'**`{prefix}allplaylists`**',
                        value='Shows you all playlists available to you',
                        inline=False)
        embed.add_field(name=f'**`{prefix}loadplaylist <playlist_name>`**',
                        value='Loads a saved playlist into the queue',
                        inline=False)
        embed.add_field(name=f'**`{prefix}saveplaylist <playlist_name>`**',
                        value='Saves all songs in the current queue',
                        inline=False)
        embed.add_field(name=f'**`{prefix}guildaddplaylist <playlist_name>`**',
                        value='Adds a playlist to a guild (you have to the playlist creator)',
                        inline=False)
        embed.add_field(name=f'**`{prefix}guildremoveplaylist <playlist_name>`**',
                        value='Removes a playlist from a guild.',
                        inline=False)
        embed.add_field(name=f'**`{prefix}deleteplaylist <playlist_name>`**',
                        value='Deletes a saved playlist (you have to the playlist creator)',
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='invite', aliases=['inv'])
    async def invite(self, ctx: commands.Context, *, args: str = ''):
        embed = Embed(
            title='\u200b',
            description=f'[Invite me](https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot'
                        f'&permissions=37088320)', colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        await ctx.send(embed=embed)

    @commands.command(name='timezone', aliases=['tz'])
    async def timezone(self, ctx: commands.Context, *, timezone=None):
        if timezone is None:
            response = requests.get(f'{self.bot.base_api_url}discord/user/',
                                    params={'id': ctx.author.id}, headers=self.bot.header).json()
            timezone = response['items'][0]['timezone'] if response.get('items') else 0
            await ctx.send(
                f':clock9: Your current timezone should be '
                f'{(datetime.utcnow() + timedelta(hours=timezone)).strftime("%H:%M")} o\'clock for you.')
            return
        try:
            timezone = int(timezone)
            if timezone < -12 or timezone > 12:
                await ctx.send('Your timezone must be between -12 and 12')
            else:
                requests.patch(f'{self.bot.base_api_url}discord/user/',
                               params={'id': ctx.author.id, 'timezone': timezone}, headers=self.bot.header)

                await ctx.send(
                    f':clock9: Successfully updated your timezone. It should be '
                    f'{(datetime.utcnow() + timedelta(hours=timezone)).strftime("%H:%M")} o\'clock for you.')
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
                requests.patch(f'{self.bot.base_api_url}discord/guild/',
                               params={'id': ctx.guild.id, 'prefix': args[1]}, headers=self.bot.header)

                await ctx.send(f':white_check_mark: Prefix set to \'**`{args[1]}`**\'')
            else:
                await ctx.send('The prefix can\'t be longer then five characters.')
        elif args[0] in ['volume', 'vol']:
            if len(args) > 1 and args[1]:
                try:
                    volume = int(args[1])
                    if 0 <= volume <= 100:
                        requests.patch(f'{self.bot.base_api_url}discord/guild/',
                                       params={'id': ctx.guild.id, 'volume': volume}, headers=self.bot.header)
                        if ctx.guild.id in self.bot.voice_states:
                            self.bot.voice_states[ctx.guild.id]._volume = volume / 100
                        await ctx.message.add_reaction('🐸')
                    else:
                        await ctx.send('The volume must be a number between 0 and 100')
                except ValueError:
                    await ctx.send('The volume must be a number')
            else:
                response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                        params={'id': ctx.guild.id}, headers=self.bot.header).json()
                if response.get('items'):
                    await ctx.send(f'The current volume is at {response["items"][0]["volume"]}/100')
        elif args[0] in ['timeout']:
            if len(args) > 1 and args[1]:
                try:
                    timeout = int(args[1])
                    if 0 <= timeout <= 6000:
                        requests.patch(f'{self.bot.base_api_url}discord/guild/',
                                       params={'id': ctx.guild.id, 'timeout': timeout}, headers=self.bot.header)
                        if ctx.guild.id in self.bot.voice_states:
                            self.bot.voice_states[ctx.guild.id].timeout = timeout
                        await ctx.message.add_reaction('🐸')
                    else:
                        await ctx.send('The timeout must be a number between 0 and 6000')
                except ValueError:
                    await ctx.send('The timeout must be a number')
            else:
                response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                        params={'id': ctx.guild.id}, headers=self.bot.header).json()
                if response.get('items'):
                    await ctx.send(f'The current timeout is set at {response["items"][0]["timeout"]} seconds')
        elif args[0] in ['musicrole', 'mr']:
            if len(args) > 1 and args[1]:
                try:
                    musicrole = int(args[1])
                    role = ctx.guild.get_role(musicrole)
                    if role:
                        requests.patch(f'{self.bot.base_api_url}discord/guild/',
                                       params={'id': ctx.guild.id, 'musicRoleId': musicrole}, headers=self.bot.header)
                        await ctx.message.add_reaction('🐸')
                    else:
                        await ctx.send('There is no role with this id in this guild.')
                except ValueError:
                    for role in ctx.guild.roles:
                        if role.name.lower() == args[1]:
                            requests.patch(f'{self.bot.base_api_url}discord/guild/',
                                           params={'id': ctx.guild.id, 'musicRoleId': role.id}, headers=self.bot.header)
                            await ctx.message.add_reaction('🐸')
                            break
                    else:
                        await ctx.send('The music role must be a number or its name.')
            else:
                await ctx.send('You must specify the roles name or id')
        elif args[0] in ['musicchannel', 'mc']:
            if len(args) > 1 and args[1]:
                try:
                    music_channel_id = int(args[1])
                    channel = ctx.guild.get_channel(music_channel_id)
                    if channel and channel.type == ChannelType.text:
                        requests.patch(
                            f'{self.bot.base_api_url}discord/guild/',
                            params={'id': ctx.guild.id, 'musicChannelId': music_channel_id},
                            headers=self.bot.header)
                        if ctx.guild.id in self.bot.voice_states:
                            self.bot.voice_states[ctx.guild.id].music_channel_id = music_channel_id

                        await ctx.message.add_reaction('🐸')
                    else:
                        await ctx.send('There is no text channel with this id in this guild.')
                except ValueError:
                    if args[1] == 'here':
                        requests.patch(
                            f'{self.bot.base_api_url}discord/guild/',
                            params={'id': ctx.guild.id, 'musicChannelId': ctx.channel.id},
                            headers=self.bot.header)
                        if ctx.guild.id in self.bot.voice_states:
                            self.bot.voice_states[ctx.guild.id].music_channel_id = ctx.channel.id

                        await ctx.message.add_reaction('🐸')
                    else:
                        await ctx.send('The music channel must be a number or \'here\'')
            else:
                await ctx.send('You must specify a channel with its id or \'here\'')
        elif args[0] in ['reset']:
            if len(args) > 1:
                if args[1] == 'all':
                    requests.patch(f'{self.bot.base_api_url}discord/guild/',
                                   params={'id': ctx.guild.id,
                                           'prefix': '!',
                                           'volume': 50,
                                           'timeout': 300,
                                           'musicRoleId': 0,
                                           'musicChannelId': 0},
                                   headers=self.bot.header)
                    if ctx.guild.id in self.bot.voice_states:
                        self.bot.voice_states[ctx.guild.id].music_channel_id = 0
                        self.bot.voice_states[ctx.guild.id]._volume = 0.5
                        self.bot.voice_states[ctx.guild.id].timeout = 300
                    await ctx.send(f':white_check_mark: Reset all settings for this guild.')
                elif args[1] == 'prefix':
                    requests.patch(f'{self.bot.base_api_url}discord/guild/',
                                   params={'id': ctx.guild.id,
                                           'prefix': '!'},
                                   headers=self.bot.header)
                    await ctx.send(f':white_check_mark: Reset prefix to **`!`**')
                elif args[1] == 'volume':
                    requests.patch(f'{self.bot.base_api_url}discord/guild/',
                                   params={'id': ctx.guild.id,
                                           'volume': 50},
                                   headers=self.bot.header)
                    if ctx.guild.id in self.bot.voice_states:
                        self.bot.voice_states[ctx.guild.id]._volume = 0.5
                    await ctx.send(f':white_check_mark: Reset volume to **`50`**')
                elif args[1] == 'musicrole':
                    requests.patch(f'{self.bot.base_api_url}discord/guild/',
                                   params={'id': ctx.guild.id,
                                           'musicRoleId': 0},
                                   headers=self.bot.header)
                    await ctx.send(f':white_check_mark: Reset music role')
                elif args[1] == 'musicchannel':
                    requests.patch(f'{self.bot.base_api_url}discord/guild/',
                                   params={'id': ctx.guild.id,
                                           'musicChannelId': 0},
                                   headers=self.bot.header)
                    if ctx.guild.id in self.bot.voice_states:
                        self.bot.voice_states[ctx.guild.id].music_channel_id = 0
                    await ctx.send(f':white_check_mark: Reset music channel')
                elif args[1] == 'timeout':
                    requests.patch(f'{self.bot.base_api_url}discord/guild/',
                                   params={'id': ctx.guild.id,
                                           'timeout': 300},
                                   headers=self.bot.header)
                    if ctx.guild.id in self.bot.voice_states:
                        self.bot.voice_states[ctx.guild.id].timeout = 300
                    await ctx.send(f':white_check_mark: Reset bot timeout to 300 seconds')
            else:
                response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                        params={'id': ctx.guild.id}, headers=self.bot.header).json()
                prefix = response['items'][0]['prefix'] if response.get('items') else '!'
                embed = Embed(title='Reset',
                              description=f'Resets settings for the bot in this guild.',
                              colour=Colour.blue())
                embed.set_thumbnail(url=self.bot.logo_url)
                embed.add_field(
                    name='Command:',
                    value=f'**`{prefix}settings reset <all/prefix/volume/musicrole/musicchannel/timeout>`**',
                    inline=False)
                await ctx.send(embed=embed)
        else:
            response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                    params={'id': ctx.guild.id}, headers=self.bot.header).json()
            prefix = response['items'][0]['prefix'] if response.get('items') else '!'
            embed = Embed(title=':gear: Frogbot settings',
                          description='Use this command to customize this bot.',
                          colour=Colour.blue())
            embed.set_thumbnail(url=self.bot.logo_url)
            embed.add_field(name='Prefix:',
                            value=f'**`{prefix}settings prefix <prefix>`**',
                            inline=False)
            embed.add_field(name='Timeout:',
                            value=f'**`{prefix}settings timeout <timeout>`**',
                            inline=False)
            embed.add_field(name='Volume:',
                            value=f'**`{prefix}settings volume <volume>`**',
                            inline=False)
            embed.add_field(name='Music Channel:',
                            value=f'**`{prefix}settings musicchannel <music_channel_id or \'here\'>`**',
                            inline=False)
            embed.add_field(name='Music Role:',
                            value=f'**`{prefix}settings musicrole <music_role_id or its name>`**',
                            inline=False)
            embed.add_field(name='Reset:',
                            value=f'**`{prefix}settings reset <option to reset>`**',
                            inline=False)
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if not message.author.bot and message.content.find(f'<@!{self.bot.user.id}>') != -1:
            if message.guild:
                response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                        params={'id': message.guild.id}, headers=self.bot.header).json()
                prefix = response['items'][0]['prefix'] if response.get('items') else '!'
                await message.channel.send(f'My current prefix is **`{prefix}`**')
            else:
                await message.channel.send(f'My current prefix is **`!`**')
