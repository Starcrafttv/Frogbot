import cassiopeia as cass
import discord
from discord.ext import commands
from src.bot.__tokens__ import __tokens__

# Not working
# Just a blueprint if I want to use it someday

# TODO work on a game command and a better display


class lolStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        cass.set_riot_api_key(__tokens__['lol'])
        cass.print_calls = False

    @commands.command(name='lolVerify', aliases=['verify', 'ver'])
    async def lolVerify(self, ctx, *, args):
        if ctx.author.bot:
            return
        elif args == '':
            await ctx.message.reply(f'Add your summonername behind the command together with the abbreviation of your region like this \'!verify username EUW\'. You also need to set your Discord ID \'{ctx.author.id}\' as a verification code in your client.', mention_author=False)
            return

        for x in ['BR', 'EUNE', 'EUW', 'LAN', 'LAS', 'NA', 'OCE', 'RU', 'TR', 'JP', 'KR']:
            if args.split(' ')[-1].upper() == x:
                region = x
                summonerName = args[:-(len(region)+1)].lower()
                break
        else:
            region = 'EUW'
            summonerName = args.lower()

        try:
            summoner = cass.get_summoner(name=summonerName, region=region)
        except Exception as _:
            await ctx.message.reply(f'Couldn\'t find the summoner {summonerName} on {region}', mention_author=False)
            return

        self.bot.c.execute(f'SELECT puuid FROM lol_links WHERE puuid = \'{summoner.puuid}\'')
        if self.bot.c.fetchone():
            await ctx.message.reply('This League of Legends account is already linked to a different discord account', mention_author=False)
            return
        try:
            if str(ctx.author.id) == summoner.verification_string:
                # self.bot.db.query('')
                # with self.bot.conn:
                #    self.bot.c.execute(
                #       f'INSERT INTO lol_links (SummonerName, Region, DiscordID, puuid) VALUES (\'{summonerName}\', \'{region}\', {ctx.author.id}, \'{summoner.puuid}\')')
                await ctx.message.add_reaction('✅')
            else:
                await ctx.message.reply(f'No verificationcode found for {summonerName} on {region}. Please set your Discord ID \'{ctx.author.id}\' in the client as a verification code.', mention_author=False)
        except Exception as e:
            print(e)

    @commands.command(name='lolStats', aliases=['lolstatss', 'lol'])
    async def lol(self, ctx, name=None):
        if ctx.author.bot:
            return

        accounts = []
        try:
            if name:
                self.bot.c.execute(
                    f'SELECT ID FROM users WHERE Username LIKE \'%{name.lower()}%\' or ID LIKE \'%{name}%\'')
                for id in self.bot.c.fetchall():
                    self.bot.c.execute(f'SELECT SummonerName, Region FROM lol_links WHERE DiscordID = {id[0]}')
                    accounts.extend(self.bot.c.fetchall())
                if not accounts:
                    await ctx.message.reply('Couldn\'t find any accounts.', mention_author=False)
            else:
                self.bot.c.execute(f'SELECT SummonerName, Region FROM lol_links WHERE DiscordID = {ctx.author.id}')
                accounts = self.bot.c.fetchall()
                if not accounts:
                    await ctx.message.reply('Your discord account isn\'t linked to any League of Legends account. Use the verify command to link your account.', mention_author=False)
        except Exception as e:
            print(e)

        for account in accounts:
            summoner = cass.get_summoner(name=account[0], region=account[1])

            matches = summoner.match_history
            masteries = summoner.champion_masteries

            embed = discord.Embed(title=summoner.name,
                                  description=f'Level: {summoner.level}\n'
                                              f'Matches played: {len(matches)}\n'
                                              f'Time played: {self.sec_to_time(len(matches)*1980)}',
                                  inline=False,
                                  colour=discord.Colour.gold())
            embed.add_field(name='Most played champions:',
                            value=f'{masteries[0].champion.name}: {masteries[0].points}\n'
                                  f'{masteries[1].champion.name}: {masteries[1].points}\n'
                                  f'{masteries[2].champion.name}: {masteries[2].points}',
                            inline=False)
            await ctx.send(embed=embed)

    @commands.command(name='game', aliases=['games', 'recent'])
    async def games(self, ctx, *, args=''):
        if ctx.author.bot:
            return
        games = 1
        name = None
        for arg in args.lower().split(' '):
            try:
                games = int(arg)
            except Exception as _:
                name = arg
        accounts = []
        if name:
            self.bot.c.execute(f'SELECT ID FROM users WHERE Username LIKE \'%{name.lower()}%\' or ID LIKE \'%{name}%\'')
            for id in self.bot.c.fetchall():
                self.bot.c.execute(f'SELECT SummonerName, Region FROM lol_links WHERE DiscordID = {id[0]}')
                accounts.extend(self.bot.c.fetchall())
        else:
            self.bot.c.execute(f'SELECT SummonerName, Region FROM lol_links WHERE DiscordID = {ctx.author.id}')
            accounts = self.bot.c.fetchall()

        for account in accounts:
            summoner = cass.get_summoner(name=account[0], region=account[1])
            try:
                embed = discord.Embed(title=summoner.name,
                                      colour=discord.Colour.green())
                for match in summoner.match_history[:games+1]:
                    print(match.creation)
                    player = match.participants[summoner]
                    embed.add_field(name=player.champion.name,
                                    value=f'KDA: {player.stats.kills}/{player.stats.deaths}/{player.stats.assists}\n'
                                    f'Game time: {self.sec_to_time(match.duration.seconds)}\n'
                                    f'Gold: {player.stats.gold_earned}\n'
                                    f'Level: {player.stats.level}\n'
                                    f'Damage: {player.stats.total_damage_dealt_to_champions}',
                                    inline=False)
                await ctx.send(embed=embed)
            except Exception as e:
                print(e)

    def sec_to_time(self, sec):
        # Convert seconds to a normalized string
        m, s = divmod(round(sec), 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        if d > 1:
            if s < 10:
                s = f'0{s}'
            if m < 10:
                m = f'0{m}'
            return f'{d} days, {h}:{m}:{s}'
        elif d == 1:
            if s < 10:
                s = f'0{s}'
            if m < 10:
                m = f'0{m}'
            return f'{d} day, {h}:{m}:{s}'
        elif h > 0:
            if s < 10:
                s = f'0{s}'
            if m < 10:
                m = f'0{m}'
            return f'{h}:{m}:{s}'
        elif m > 0:
            if s < 10:
                s = f'0{s}'
            return f'{m}:{s}'
        else:
            return f'{s}'
