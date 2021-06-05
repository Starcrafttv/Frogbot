from bot.utils.get_last_days import get_last_days
from bot.utils.plot_py import get_leaderboard
from bot.utils.secToTime import sec2time
from discord import Colour, Embed, File
from discord.ext import commands


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='leaderboard', aliases=['lb', 'lboard'])
    @commands.guild_only()
    async def leaderboard(self, ctx, *, args=''):
        if ctx.author.bot:
            return
        top = 5
        requestedDays = 0
        total = False
        plot = False
        time_type = True
        r_type = 1
        for arg in args.split(' '):
            arg = arg.lower().strip(' _#!<@>').replace("'", '`')
            if arg:
                if arg in ['plot', 'plt']:
                    plot = True
                elif arg in ['global', 'total']:
                    self.bot.c.execute(f"SELECT UserPrivileges FROM users WHERE UserID = '{ctx.author.id}'")
                    if self.bot.c.fetchone()[0] >= 7:
                        total = True
                elif arg in ['active', 'online']:
                    r_type = 1
                elif arg in ['afk']:
                    r_type = 2
                elif arg in ['messages', 'message']:
                    r_type = 3
                elif arg.strip('01234567890') in ['last=', 'days='] and len(arg) > 4:
                    try:
                        requestedDays = int(arg[5:])
                    except ValueError:
                        pass

        if requestedDays > 365:
            await ctx.send("You can't request more then 365 days.")
            return
        elif requestedDays < 0:
            await ctx.send("You can't request less then one day.")
            return
        if top > 15:
            await ctx.send("You can't request more then 15 positions.")
            return
        elif top < 1:
            await ctx.send("You can't request less then one position.")
            return

        if r_type == 1:
            description = f'Active time for the last {requestedDays} days' if requestedDays else 'Total active time'
            value = 'Active time: '
        elif r_type == 2:
            description = f'Afk time for the last {requestedDays} days' if requestedDays else 'Total afk time'
            value = 'Afk time: '
        else:
            description = f'Messages sent for the last {requestedDays} days' if requestedDays else 'Total messages sent'
            value = 'Messages: '
            time_type = False

        leaderboard = []
        for member in ctx.guild.members:
            if not member.bot:
                stats = get_last_days(
                    self.bot.c, member.id, f'{member.name}#{member.discriminator}', requestedDays, ctx.guild.id
                    if not total else False)
                leaderboard.append([stats[0][1], sum(day[r_type]
                                                     for day in stats[1:]) if requestedDays else stats[0][r_type+1]])
        leaderboard = sorted(leaderboard, key=lambda user: user[1], reverse=True)[:top]

        if plot:
            if get_leaderboard(
                [user[0] for user in reversed(leaderboard)],
                [round(user[1]/86400, 3) for user in reversed(leaderboard)],
                    top, time_type, description):
                await ctx.send(file=File('bot/data/temp/stats.png', filename='stats.png'))
        else:
            embed = Embed(title='Leaderboard:',
                          description=description,
                          inline=False,
                          colour=Colour.blue())
            for user in leaderboard:
                embed.add_field(name=user[0],
                                value=value + str(sec2time(user[1])) if time_type else str(user[1]),
                                inline=False)
            await ctx.send(embed=embed)
