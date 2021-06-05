from datetime import datetime, timedelta

from bot.utils.get_last_days import get_last_days
from bot.utils.plot_py import get_compare
from discord import File
from discord.ext import commands


class Compare(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='compare', aliases=['comp'])
    @commands.guild_only()
    async def compare(self, ctx, *, args):
        if ctx.author.bot:
            return
        # Get all information out of the inputs from the user
        r_type = 1
        requestedDays = 10
        user_ids = []
        total = False
        for arg in args.split(' '):
            arg = arg.lower().strip(' _#!<@>')
            if arg:
                if arg in ['global', 'total']:
                    self.bot.c.execute(f"SELECT UserPrivileges FROM users WHERE UserID = '{ctx.author.id}'")
                    if self.bot.c.fetchone()[0] >= 7:
                        total = True
                elif arg in ['active', 'online']:
                    r_type = 1
                elif arg in ['afk']:
                    r_type = 2
                elif arg in ['messages', 'message']:
                    r_type = 3
                else:
                    try:
                        requestedDays = int(arg)
                    except ValueError:
                        for member in ctx.guild.members:
                            if f'{member.name}#{member.discriminator}'.lower().find(arg) != -1:
                                user_ids.append(member.id)
        # Test if there are any problems with the inputs
        if requestedDays < 1:
            await ctx.send("You can't request less then one day.")
            return
        elif requestedDays > 365:
            await ctx.send("You can't request more then 365 days.")
            return
        user_ids = [i for n, i in enumerate(user_ids) if i not in user_ids[:n]]
        if len(user_ids) > 5:
            await ctx.send("You can't request more then five users.")
            return
        elif len(user_ids) < 1:
            await ctx.send('You need to request at least two users.')
            return
        elif len(user_ids) <= 1:
            await ctx.send('You need to select more then one other user.')
            return
        # Get the dates for all requested days
        self.bot.c.execute(f"SELECT Timezone FROM users WHERE UserID = '{ctx.author.id}'")
        timezone = self.bot.c.fetchone()[0]
        date_list = []
        for i in range(requestedDays-1, -1, -1):
            y, m, d = str((datetime.utcnow() + timedelta(days=-i, hours=timezone)).date()).split('-')
            date_list.append(f'{d}.{m}.{y[2:]}')
        # Get all stats for each user requested
        user_stats = []
        usernames = []
        for id in user_ids:
            username = f'{self.bot.client.get_user(id).name}#{self.bot.client.get_user(id).discriminator}'
            stats = get_last_days(self.bot.c, id, username, requestedDays, ctx.guild.id
                                  if not total and ctx.guild else False)
            usernames.append(username)
            user_stats.append([day[r_type] / (1 if r_type == 3 else 3600) for day in reversed(stats[1:])])
        # Try to create a graph and then send it back to the user
        if get_compare(usernames, user_stats, date_list, r_type):
            await ctx.send('', file=File('bot/data/temp/stats.png', filename='bot/data/temp/stats.png'))
