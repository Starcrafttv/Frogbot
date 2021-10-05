import requests
from nextcord import Colour, Embed
from nextcord.ext import commands
from src.bot.bot import Bot
from src.stats.sec_to_time import sec_to_time
from src.stats.stats import get_last_days


class Average(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name='average', aliases=['avg'])
    async def average(self, ctx: commands.Context, *, args: str = ''):
        if ctx.author.bot:
            return
        # Format all user command inputs into who and last_days
        requested_days = 10
        other_user = False
        total = False
        for arg in args.split(' '):
            arg = arg.lower().strip(' _#!<@>')
            if arg:
                if arg in ['global', 'total']:
                    total = True
                else:
                    try:
                        requested_days = int(arg)
                    except ValueError:
                        response = requests.get(f'{self.bot.base_api_url}discord/user/',
                                                params={'id': ctx.author.id}, headers=self.bot.header).json()
                        if response.get('items') and response['items'][0]['privileges'] >= 7:
                            other_user = arg
        # Check if too many or little days are requested
        if requested_days > 150:
            await ctx.send('Sorry, but you can´t requested more then 150 days.')
            return
        elif requested_days < 1:
            await ctx.send('Sorry, but you can´t requested less then 1 day.')
            return
        # Get the users name and id
        if other_user and ctx.guild:
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
        # Get the stats
        stats = await get_last_days(user_id, username, requested_days,
                                    ctx.guild.id if not total and ctx.guild else False)

        # Create an embed and calculate the averages
        embed = Embed(title=username,
                      description=f'Averages for last {requested_days} days:',
                      colour=Colour.blue())
        embed.add_field(name='Active time:',
                        value=f'{await sec_to_time(sum(day[1] for day in stats[1:]) / requested_days)} per day',
                        inline=False)
        embed.add_field(name='Afk time:',
                        value=f'{await sec_to_time(sum(day[2] for day in stats[1:]) / requested_days)} per day',
                        inline=False)
        embed.add_field(name='Messages sent:',
                        value=f'{round(sum(day[3] for day in stats[1:]) / requested_days)} per day',
                        inline=False)
        # Send the embed in the channel where the message came from
        await ctx.send(embed=embed)
