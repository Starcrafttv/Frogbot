import requests
import src.stats.plot as plt
import src.stats.stats as util
from nextcord import Colour, Embed, File
from nextcord.ext import commands
from src.bot.bot import Bot
from src.stats.sec_to_time import sec_to_time


class Stats(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name='stats', aliases=['info', 'stts', 'sts'])
    async def _stats(self, ctx: commands.Context, *, args: str = ''):
        if ctx.author.bot:
            return

        other_user = False
        requested_days = 1
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
                        requested_days = int(arg)
                    except ValueError:
                        response = requests.get(f'{self.bot.base_api_url}discord/user/',
                                                params={'id': ctx.author.id}, headers=self.bot.header).json()
                        if response.get('items') and response['items'][0]['privileges'] >= 7:
                            other_user = arg

        if requested_days > 100:
            await ctx.send('Sorry, but you can\'t requested more then 100 days.')
            return
        elif requested_days < 1:
            await ctx.send('Sorry, but you can\'t requested less then 1 day.')
            return

        if other_user:
            for member in ctx.guild.members:
                if f'{member.name}#{member.discriminator}'.lower().find(other_user) != -1:
                    username = f'{member.name}#{member.discriminator}'
                    user_id = member.id
                    break
            else:
                await ctx.send(f'User \'{other_user}\' not found.')
                return
        else:
            username = f'{ctx.author.name}#{ctx.author.discriminator}'
            user_id = ctx.author.id

        stats = await util.get_last_days(user_id, username, requested_days,
                                         ctx.guild.id if not total and ctx.guild else False, raw)

        if raw:

            if await plt.get_raw_stats(stats[0], stats[1], stats[2], stats[3], stats[4]):
                await ctx.send('', file=File('data/temp/stats.png', filename='stats.png'))
        elif plot:
            if await plt.get_stats(stats):
                await ctx.send('', file=File('data/temp/stats.png', filename='stats.png'))
        else:
            embed = Embed(
                title=username,
                description=f'Total active time: {await sec_to_time(stats[0][2])}\n'
                            f'Total afk Time: {await sec_to_time(stats[0][3])}\n'
                            f'Total messages sent: {stats[0][4]}', colour=Colour.blue())
            for day in stats[1:]:
                y, m, d = day[0].split('-')
                embed.add_field(name=f'{d}.{m}.{y[2:]}:',
                                value=f'- Active time: {await sec_to_time(day[1])}\n'
                                      f'- Afk time: {await sec_to_time(day[2])}\n'
                                      f'- Messages sent: {day[3]}',
                                inline=False)
            await ctx.send(embed=embed)
