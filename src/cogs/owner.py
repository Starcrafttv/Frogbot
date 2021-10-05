import requests
from nextcord.ext import commands
from nextcord.message import Message
from src.bot.bot import Bot


class Owner(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name='setPermissions', hidden=True, aliases=['setp'])
    @commands.is_owner()
    async def setPermissions(self, ctx: commands.Context, arg: str, id: int, rights: int):
        # Change a users rights or guilds rights
        arg = arg.lower().strip(' <>!@')
        if arg in ['userrights', 'u_permissions', 'u_p']:
            requests.patch(f'{self.bot.base_api_url}discord/user/',
                           params={'id': ctx.guild.id, 'privileges': rights}, headers=self.bot.header)
            await ctx.send(f'Set  user privileges level for {id} to {rights}')
        elif arg in ['guildrights', 'g_permissions', 'g_p']:
            requests.patch(f'{self.bot.base_api_url}discord/guild/',
                           params={'id': ctx.guild.id, 'privileges': rights}, headers=self.bot.header)
            await ctx.send(f'Set guild privileges for {id} to {rights}')

    @commands.command(name='setStatus', hidden=True)
    @commands.is_owner()
    async def set_status(self, ctx: commands.Context, _type: str = '', message: str = ''):
        if not _type:
            await ctx.send('Choose between '
                           '\'s\' - streaming, '
                           '\'p\' - playing, '
                           '\'w\' - watching and '
                           '\'l\' - listening to')
        elif not message:
            await ctx.send('You have to choose a message after the selected type of status.')
        else:
            await self.bot.set_status(_type, message)
            await ctx.message.add_reaction('🐸')

    @commands.command(name='guilds', hidden=True)
    @commands.is_owner()
    async def _guilds(self, ctx: commands.Context, arg: str = ''):
        if arg == '':
            await ctx.send(f'I am currently in {len(self.bot.guilds)} guilds.')
        elif arg == 'new':
            await ctx.send(f'This function is currently being built...')
        elif arg == 'voice':
            await ctx.send('All guilds I am currently connected to:')
            message = ''
            n = 50
            for i, guild_id in enumerate(self.bot.voice_states):
                guild = self.bot.get_guild(guild_id)
                message += f'{i+1}. \'{guild.name}\', {guild.member_count}\n'

                if i > n:
                    n += 50
                    await ctx.send(f'```{message}```')
                    message = ''
            if message:
                await ctx.send(f'```{message}```')
        else:
            await ctx.send('All guilds I am currently in:')
            message = ''
            n = 50
            for i, guild in enumerate(sorted(self.bot.guilds, key=lambda guild: guild.member_count, reverse=True)):
                message += f'{i+1}. \'{guild.name}\', {guild.member_count}\n'

                if i > n:
                    n += 50
                    await ctx.send(f'```{message}```')
                    message = ''
            if message:
                await ctx.send(f'```{message}```')
