import src.stats.plot as plt
import src.stats.stats as util
from discord import Colour, Embed, File
from discord.ext import commands
from src.bot.bot import Bot
from src.stats.sec_to_time import sec_to_time


class Stats(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name='stats', aliases=['info', 'stts', 'sts'])
    async def _stats(self, ctx: commands.Context, *, args: str = ''):
        if ctx.author.bot:
            return

        OtherUser = False
        requestedDays = 1
        plot = False
        raw = False
        total = False
        for arg in args.split(' '):
            arg = arg.lower().strip(' _#!<@>')
            if arg:
                if arg in ['plot', 'plt']:
                    plot = True
                elif arg in ['raw', 'detailed', 'exact', '+']:
                    raw = True
                elif arg in ['global', 'total', 'all']:
                    total = True
                else:
                    try:
                        requestedDays = int(arg)
                    except ValueError:
                        self.bot.c.execute(f"SELECT UserPrivileges FROM users WHERE UserID = {ctx.author.id}")
                        if self.bot.c.fetchone()[0] >= 7:
                            OtherUser = arg

        if requestedDays > 100:
            await ctx.send("Sorry, but you can't requested more then 100 days.")
            return
        elif requestedDays < 1:
            await ctx.send("Sorry, but you can't requested less then 1 day.")
            return

        if OtherUser:
            for member in ctx.guild.members:
                if f'{member.name}#{member.discriminator}'.lower().find(OtherUser) != -1:
                    username = f'{member.name}#{member.discriminator}'
                    userID = member.id
                    break
            else:
                await ctx.send(f"User '{OtherUser}' not found.")
                return
        else:
            username = f'{ctx.author.name}#{ctx.author.discriminator}'
            userID = ctx.author.id

        stats = util.get_last_days(self.bot.c, userID, username, requestedDays,
                                   ctx.guild.id if not total and ctx.guild else False, raw)

        if raw:
            if plt.get_raw_stats(stats[0], stats[1], stats[2], stats[3], stats[4]):
                await ctx.send('', file=File('data/temp/stats.png', filename='stats.png'))
        elif plot:
            if plt.get_stats(stats):
                await ctx.send('', file=File('data/temp/stats.png', filename='stats.png'))
        else:
            embed = Embed(
                title=username,
                description=f'Total active time: {sec_to_time(stats[0][2])}\n'
                f'Total afk Time: {sec_to_time(stats[0][3])}\n'
                f'Total messages sent: {stats[0][4]}', inline=False, colour=Colour.blue())
            for day in stats[1:]:
                y, m, d = day[0].split('-')
                embed.add_field(name=f'{d}.{m}.{y[2:]}:',
                                value=f'- Active time: {sec_to_time(day[1])}\n'
                                      f'- Afk time: {sec_to_time(day[2])}\n'
                                      f'- Messages sent: {day[3]}',
                                inline=False)
            await ctx.send(embed=embed)