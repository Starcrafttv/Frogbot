from discord.ext import commands
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
            with self.bot.conn:
                self.bot.c.execute(f'UPDATE users SET UserPrivileges = {rights} WHERE UserID = {id}')
            await ctx.send(f'Set  user privileges level for {id} to {rights}')
        elif arg in ['guildrights', 'g_permissions', 'g_p']:
            with self.bot.conn:
                self.bot.c.execute(f'UPDATE guilds SET GuildPrivileges = {rights} WHERE GuildID = {id}')
            await ctx.send(f'Set guild privileges for {id} to {rights}')

    @commands.command(name='setStatus', hidden=True)
    @commands.is_owner()
    async def setStatus(self, ctx: commands.Context, _type: str = '', message: str = ''):
        if not _type:
            await ctx.send('Choose between \'s\' - streaming, \'p\' - playing, \'w\' - watching and \'l\' - listening to')
        elif not message:
            await ctx.send('You have to choose a message after the selected type of status.')
        else:
            await self.bot.setStatus(_type, message)
            await ctx.message.add_reaction('🐸')
