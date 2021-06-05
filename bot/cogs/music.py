import math
import os

from bot.classes.voiceClient import VoiceClient
from discord import Colour, Embed
from discord.ext import commands


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='join', aliases=['summon', 'connect'])
    async def join(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.author.voice:
            # Join Voice Channel
            if not ctx.voice_client:
                await ctx.author.voice.channel.connect()
            elif ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.voice_client.move_to(ctx.author.voice.channel)
            if ctx.guild.id in self.bot.voiceClients:
                self.bot.voiceClients[ctx.guild.id].voiceClient = ctx.voice_client
            else:
                self.bot.voiceClients[ctx.guild.id] = VoiceClient(self.bot.client, ctx.voice_client)
                self.bot.voiceClients[ctx.guild.id].loadSavedClient(self.bot.c)
            return True
        return False

    @commands.command(name='leave', aliases=['lve', 'dc', 'disconnect'])
    async def leave(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.voice_client:
            if ctx.guild.id in self.bot.voiceClients and self.bot.voiceClients[ctx.guild.id].reactMessageId:
                message = await self.bot.client.get_channel(self.bot.voiceClients[ctx.guild.id].reactMessageChannelId).fetch_message(self.bot.voiceClients[ctx.guild.id].reactMessageId)
                await message.clear_reactions()
            await ctx.voice_client.disconnect()
            self.bot.voiceClients.pop(ctx.guild.id, None)
            return True
        return False

    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if await self.join(ctx):
            requester = f'{ctx.author.name}#{ctx.author.discriminator}'
            self.bot.voiceClients[ctx.guild.id].loadSongs(args, requester)
            await ctx.message.add_reaction('🐸')

    @commands.command(name='playtop', aliases=['pt'])
    async def playtop(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if await self.join(ctx):
            requester = f'{ctx.author.name}#{ctx.author.discriminator}'
            self.bot.voiceClients[ctx.guild.id].loadSongs(args, requester, True)
            await ctx.message.add_reaction('🐸')

    @commands.command(name='playskip', aliases=['ps'])
    async def playskip(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if await self.join(ctx):
            requester = f'{ctx.author.name}#{ctx.author.discriminator}'
            self.bot.voiceClients[ctx.guild.id].loadSongs(args, requester, True, True)
            await ctx.message.add_reaction('🐸')

    @commands.command(name='pause', aliases=['stop'])
    async def pause(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.voiceClients[ctx.guild.id].pause()
            await ctx.message.add_reaction('🐸')

    @commands.command(name='resume', aliases=['re', 'res', 'continue', 'unpause'])
    async def resume(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.voiceClients[ctx.guild.id].resume()
            await ctx.message.add_reaction('🐸')

    @commands.command(name='skip', aliases=['s', 'next'])
    async def skip(self, ctx, index: int = 1):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.voiceClients[ctx.guild.id].skip(index-1)
            await ctx.message.add_reaction('🐸')

    @commands.command(name='last', aliases=['previous'])
    async def last(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.voiceClients[ctx.guild.id].previousTrack()
            await ctx.message.add_reaction('🐸')

    @commands.command(name='replay', aliases=['rp'])
    async def replay(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.voiceClients[ctx.guild.id].replay()
            await ctx.message.add_reaction('🐸')

    @commands.command(name='remove', aliases=['rm'])
    async def remove(self, ctx, index: int):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.voiceClients[ctx.guild.id].remove(index-1)
            await ctx.message.add_reaction('🐸')

    @commands.command(name='move', aliases=['m', 'mv'])
    async def move(self, ctx, fromIndex: int, toIndex: int = 0):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.voiceClients[ctx.guild.id].move(fromIndex-1, toIndex-1)
            await ctx.message.add_reaction('🐸')

    @commands.command(name='clear', aliases=['cls'])
    async def clear(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.voiceClients[ctx.guild.id].clear()
            await ctx.message.add_reaction('🐸')

    @commands.command(name='shuffle', aliases=['random'])
    async def shuffle(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.voiceClients[ctx.guild.id].shuffle()
            await ctx.message.add_reaction('🐸')

    @commands.command(name='nowPlaying', aliases=['np'])
    @commands.guild_only()
    async def nowPlaying(self, ctx, *, args=''):
        if ctx.guild.id in self.bot.voiceClients and self.bot.voiceClients[ctx.guild.id].currentSong:
            songInfo = self.bot.voiceClients[ctx.guild.id].currentSong.getInfo()
            if not songInfo:
                return
            embed = (Embed(title=':musical_note: Now playing:',
                           description=f'[{songInfo["title"]}](http://www.youtube.com/watch?v={songInfo["id"]})',
                           color=Colour.blurple())
                     .add_field(name='Duration', value=songInfo['duration'])
                     .add_field(name='Requested by', value=songInfo['requester'])
                     .add_field(name='Creator', value=songInfo['creator'])
                     .set_thumbnail(url=songInfo['thumbnailUrl']))
            await ctx.send(embed=embed)

    @commands.command(name='grab', aliases=['yoink'])
    @commands.guild_only()
    async def grab(self, ctx, *, args=''):
        if ctx.guild.id in self.bot.voiceClients and self.bot.voiceClients[ctx.guild.id].currentSong:
            songInfo = self.bot.voiceClients[ctx.guild.id].currentSong.getInfo()
            if not songInfo:
                return
            embed = (Embed(title=':musical_note: Now playing:',
                           description=f'[{songInfo["title"]}](http://www.youtube.com/watch?v={songInfo["id"]})',
                           color=Colour.blurple())
                     .add_field(name='Duration', value=songInfo['duration'])
                     .add_field(name='Creator', value=songInfo['creator'])
                     .set_thumbnail(url=songInfo['thumbnailUrl']))
            channel = await ctx.author.create_dm()
            await channel.send(embed=embed)

    @commands.command(name='queue', aliases=['q', 'pl'])
    async def queue(self, ctx, page: int = 1, pageSize: int = 10):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            pages = math.ceil(len(self.bot.voiceClients[ctx.guild.id].queue)/pageSize)

            if page < 1:
                page = 1
            elif page > pages:
                page = pages

            start = (page-1) * pageSize
            end = start + pageSize

            embed = Embed(title=':scroll: Current Queue:',
                                description='\u200b',
                                color=Colour.blurple())
            embed.set_thumbnail(url=self.bot.logoUrl)

            if self.bot.voiceClients[ctx.guild.id].currentSong:
                songInfo = self.bot.voiceClients[ctx.guild.id].currentSong.getInfo()
                embed.add_field(name='Now playing:',
                                value=f'[{songInfo["title"]}](http://www.youtube.com/watch?v={songInfo["id"]})',
                                inline=False)

            for i, song in enumerate(self.bot.voiceClients[ctx.guild.id].queue[start:end], start=start):
                songInfo = song.getInfo()
                if songInfo:
                    embed.add_field(name=f'**`{i+1}.`** {songInfo["title"]}',
                                    value=f'By {songInfo["creator"]}, Length: {songInfo["duration"]}',
                                    inline=False)

            if self.bot.voiceClients[ctx.guild.id].queue:
                embed.add_field(name='\u200b',
                                value=f'Page {page} of {pages}',
                                inline=False)
            else:
                embed.add_field(name='Soo empty',
                                value='\u200b')

            await ctx.send(embed=embed)

    # Follow user over discord-spotify status

    @commands.command(name='follow', aliases=['f'])
    async def follow(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return

        for activity in ctx.author.activities:
            if activity.name == "Spotify":
                if await self.join(ctx):
                    self.bot.voiceClients[ctx.guild.id].follow(ctx.author.id)
                    await ctx.message.add_reaction('🐸')
                    break
        else:
            await ctx.send("Can't find your Spotify connection")

    @commands.command(name='unfollow', aliases=['uf'])
    async def unfollow(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients and self.bot.voiceClients[ctx.guild.id].following:
            self.bot.voiceClients[ctx.guild.id].following = None
            await ctx.message.add_reaction('🐸')

    # Playlists

    @commands.command(name='loadPlaylist', aliases=['pp', 'playplaylist', 'lp'])
    async def loadPlaylist(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if await self.join(ctx):
            self.bot.c.execute(
                f"SELECT PlaylistID FROM playlists WHERE PlaylistName = '{args}' AND GuildID = '{ctx.guild.id}'")
            playlistID = self.bot.c.fetchone()
            if playlistID:
                requester = f'{ctx.author.name}#{ctx.author.discriminator}'
                self.bot.voiceClients[ctx.guild.id].load(playlistID[0], requester)
                await ctx.message.add_reaction('🐸')
            else:
                await ctx.send(f"Can't find a playlist named **`{args}`**. Make sure to spell the name right.")

    @commands.command(name='saveplaylist', aliases=['sp', 'sq', 'savequeue'])
    async def saveplaylist(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.c.execute(
                f"SELECT PlaylistID FROM playlists WHERE PlaylistName = '{args}' AND GuildID = '{ctx.guild.id}'")
            playlistID = self.bot.c.fetchone()
            if playlistID:
                if os.path.isfile(f"bot/data/playlists/{playlistID[0]}.p"):
                    os.remove(f"bot/data/playlists/{playlistID[0]}.p")
                with self.bot.conn:
                    self.bot.c.execute(f"DELETE FROM playlists WHERE PlaylistID = {playlistID[0]}")
            with self.bot.conn:
                self.bot.c.execute(
                    f"INSERT INTO playlists (PlaylistName, GuildID) VALUES ('{args}', '{ctx.guild.id}')")
            self.bot.c.execute(
                f"SELECT PlaylistID FROM playlists WHERE PlaylistName = '{args}' AND GuildID = '{ctx.guild.id}'")
            self.bot.voiceClients[ctx.guild.id].save(self.bot.c.fetchone()[0])
            await ctx.send(f'Successfully saved the current playlist as **`{args}`**')

    @commands.command(name='savedplaylists', aliases=['allplaylists', 'ap'])
    async def savedplaylists(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        self.bot.c.execute(f"SELECT PlaylistName FROM playlists WHERE GuildID = '{ctx.guild.id}'")
        embed = Embed(title=':notepad_spiral: All saved playlists:',
                      description='‎‎\u200b',
                      inline=False,
                      colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logoUrl)
        for playlistname in self.bot.c.fetchall():
            embed.add_field(name=f"**`{playlistname[0]}`**", value='\u200b')
        await ctx.send(embed=embed)

    @commands.command(name='deletePlaylist', aliases=['dp', 'rmp'])
    async def deletePlaylist(self, ctx, *, args):
        if not self.hasPermissions(ctx):
            return
        self.bot.c.execute(
            f"SELECT PlaylistID FROM playlists WHERE PlaylistName = '{args}' AND GuildID = '{ctx.guild.id}'")
        playlistID = self.bot.c.fetchone()
        if playlistID:
            if os.path.isfile(f"data/playlists/{playlistID[0]}.p"):
                os.remove(f"data/playlists/{playlistID[0]}.p")
            with self.bot.conn:
                self.bot.c.execute(f"DELETE FROM playlists WHERE PlaylistID = {playlistID[0]}")
            await ctx.send(f'Successfully deleted **`{args}`**')
        else:
            await ctx.send(f"Can't find a playlist named **`{args}`**. Make sure to spell the name right.")

    @commands.command(name='ping')
    async def ping(self, ctx, *, args=''):
        embed = Embed(title='Latency',
                      description='‎‎\u200b',
                      inline=False,
                      colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logoUrl)
        embed.add_field(name='Client latency:', value=f' **`{round(self.bot.client.latency*1000)}ms`**', inline=False)
        if ctx.guild and ctx.guild.id in self.bot.voiceClients:
            embed.add_field(
                name='Voice client latency:',
                value=f' **`{round(self.bot.voiceClients[ctx.guild.id].voiceClient.latency*1000)}ms`**',
                inline=False)
            embed.add_field(
                name=f'Average voice client latency:',
                value=f' **`{round(self.bot.voiceClients[ctx.guild.id].voiceClient.average_latency*1000)}ms`**',
                inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='loopSong', aliases=['ls'])
    async def loopSong(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.voiceClients[ctx.guild.id].loopSong = not self.bot.voiceClients[ctx.guild.id].loopSong
            self.bot.voiceClients[ctx.guild.id].loopQueue = False
            await ctx.message.add_reaction('🐸')

    @commands.command(name='loopQueue', aliases=['lq'])
    async def loopQueue(self, ctx, *, args=''):
        if not self.hasPermissions(ctx):
            return
        if ctx.guild.id in self.bot.voiceClients:
            self.bot.voiceClients[ctx.guild.id].loopQueue = not self.bot.voiceClients[ctx.guild.id].loopQueue
            self.bot.voiceClients[ctx.guild.id].loopSong = False
            await ctx.message.add_reaction('🐸')

    def hasPermissions(self, ctx):
        if ctx.guild:
            self.bot.c.execute(f"SELECT ReqRole FROM guilds WHERE GuildID = '{ctx.guild.id}'")
            reqRole = self.bot.c.fetchone()
            if reqRole and reqRole[0]:
                return ctx.guild.get_role(reqRole[0]) in ctx.author.roles
            else:
                return True
        return False
