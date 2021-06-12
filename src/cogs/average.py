from discord import Colour, Embed
from discord.ext import commands
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
        requestedDays = 10
        OtherUser = False
        total = False
        for arg in args.split(' '):
            arg = arg.lower().strip(' _#!<@>')
            if arg:
                if arg in ['global', 'total']:
                    total = True
                else:
                    try:
                        requestedDays = int(arg)
                    except ValueError:
                        self.bot.c.execute(f"SELECT UserPrivileges FROM users WHERE UserID = {ctx.author.id}")
                        if self.bot.c.fetchone()[0] >= 7:
                            OtherUser = arg
        # Check if too many or little days are requested
        if requestedDays > 150:
            await ctx.send('Sorry, but you can´t requested more then 150 days.')
            return
        elif requestedDays < 1:
            await ctx.send('Sorry, but you can´t requested less then 1 day.')
            return
        # Get the users name and id
        if OtherUser and ctx.guild:
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
        # Get the stats
        stats = get_last_days(self.bot.c, userID, username, requestedDays,
                              ctx.guild.id if not total and ctx.guild else False)

        # Create an embed and calculate the averages
        embed = Embed(title=username,
                      description=f'Averages for last {requestedDays} days:',
                      inline=False,
                      colour=Colour.blue())
        embed.add_field(name='Active time:',
                        value=f'{sec_to_time(sum(day[1] for day in stats[1:]) / requestedDays)} per day',
                        inline=False)
        embed.add_field(name='Afk time:',
                        value=f'{sec_to_time(sum(day[2] for day in stats[1:]) / requestedDays)} per day',
                        inline=False)
        embed.add_field(name='Messages sent:',
                        value=f'{round(sum(day[3] for day in stats[1:]) / requestedDays)} per day',
                        inline=False)
        # Send the embed in the channel where the message came from
        await ctx.send(embed=embed)
