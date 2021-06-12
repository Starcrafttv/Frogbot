import os

import discord
import src.music.search as search
from discord.ext import commands
from src.music.voicestate import VoiceState


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_voice_state(self, ctx: commands.Context) -> VoiceState:
        state = self.bot.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx.guild.id)
            self.bot.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.bot.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        self.bot.c.execute(f"SELECT ReqRole FROM guilds WHERE GuildID = '{ctx.guild.id}'")
        reqRole = self.bot.c.fetchone()
        if reqRole and reqRole[0]:
            if not ctx.guild.get_role(reqRole[0]) in ctx.author.roles:
                raise commands.MissingPermissions('You need permissions to use this command.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send(f'An error occurred: {error}')

    # Commands

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['dc'])
    async def _leave(self, ctx: commands.Context):
        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await ctx.voice_state.stop()
        del self.bot.voice_states[ctx.guild.id]

    @commands.command(name='play', aliases=['p'])
    async def _play(self, ctx: commands.Context, *, query: str = ''):
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        if not query:
            return

        async with ctx.typing():
            try:
                songs = search.get_songs(ctx.author, query)
            except Exception as e:
                await ctx.send(f'An error occurred while processing this request: {e}')
            else:
                ctx.voice_state.queue += songs
                await self.play_command_message(ctx, songs)

    @commands.command(name='playtop', aliases=['pt'])
    async def _playtop(self, ctx: commands.Context, *, query: str = ''):
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        if not query:
            return

        async with ctx.typing():
            try:
                songs = search.get_songs(ctx.author, query)
            except Exception as e:
                await ctx.send(f'An error occurred while processing this request: {e}')
            else:
                ctx.voice_state.queue = songs + ctx.voice_state.queue
                await self.play_command_message(ctx, songs)

    @commands.command(name='playskip', aliases=['ps'])
    async def _playskip(self, ctx: commands.Context, *, query: str = ''):
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                songs = search.get_songs(ctx.author, query)
            except Exception as e:
                await ctx.send(f'An error occurred while processing this request: {e}')
            else:
                ctx.voice_state.queue = songs + ctx.voice_state.queue
                ctx.voice_state.skip()
                await self.play_command_message(ctx, songs)

    async def play_command_message(self, ctx: commands.Context, songs: list):
        if len(songs) == 1:
            embed = discord.Embed(
                title=f'Added song to queue:',
                description=f'[{songs[0].title}]({songs[0].url})\nCreator: {songs[0].channel_title}, Duration: {songs[0].duration_str}',
                inline=False, colour=discord.Colour.blue())
            embed.set_thumbnail(url=self.bot.logo_url)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f'Added {len(songs)} songs to queue',
                description=f'1. ‎[{songs[0].title}]({songs[0].url})\n...\n{len(songs)}. ‎‎[{songs[-1].title}]({songs[-1].url})',
                inline=False, colour=discord.Colour.blue())
            embed.set_thumbnail(url=self.bot.logo_url)
            await ctx.send(embed=embed)

    @commands.command(name='skip', aliases=['s'])
    async def _skip(self, ctx: commands.Context, *, args: str = ''):
        if ctx.voice_state.voice:
            ctx.voice_state.skip()
            await ctx.message.add_reaction('🐸')

    @commands.command(name='pause', aliases=['pse'])
    async def _pause(self, ctx: commands.Context, *, args: str = ''):
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('🐸')

    @commands.command(name='resume', aliases=['res'])
    async def _resume(self, ctx: commands.Context, *, args: str = ''):
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('🐸')

    @commands.command(name='shuffle', aliases=['random'])
    async def _shuffle(self, ctx: commands.Context, *, args: str = ''):
        ctx.voice_state.shuffle()
        await ctx.message.add_reaction('🐸')

    @commands.command(name='remove', aliases=['rm'])
    async def _remove(self, ctx: commands.Context, index: int = 1):
        if len(ctx.voice_state.queue) and 0 <= index - 1 <= len(ctx.voice_state.queue):
            ctx.voice_state.queue.pop(index-1)
            await ctx.message.add_reaction('🐸')

    @commands.command(name='move', aliases=['m'])
    async def _move(self, ctx: commands.Context, from_index: int, to_index: int = 1):
        if len(ctx.voice_state.queue):
            if 0 <= from_index - 1 <= len(ctx.voice_state.queue) and 0 <= to_index - 1 <= len(ctx.voice_state.queue):
                song = ctx.voice_state.queue.pop(from_index-1)
                ctx.voice_state.queue.insert(to_index - 1, song)
                await ctx.message.add_reaction('🐸')

    @commands.command(name='loopsong', aliases=['ls'])
    async def _loopsong(self, ctx: commands.Context, *, args: str = ''):
        if not ctx.voice_state.current_song:
            return
        if ctx.voice_state._loop_song:
            ctx.voice_state._loop_song = False
            ctx.voice_state._loop_queue = False
            await ctx.send('Stopped the loop of eternity')
        else:
            ctx.voice_state._loop_song = True
            ctx.voice_state._loop_queue = False

            await ctx.send(f'Repeating **{ctx.voice_state.current_song.title}** for ever.')

    @commands.command(name='loopqueue', aliases=['lq'])
    async def _loopqueue(self, ctx: commands.Context, *, args: str = ''):
        if ctx.voice_state._loop_queue:
            ctx.voice_state._loop_song = False
            ctx.voice_state._loop_queue = False
            await ctx.send('Stopped the loop of eternity')
        else:
            ctx.voice_state._loop_song = False
            ctx.voice_state._loop_queue = True

            await ctx.send(f'Repeating these **{len(ctx.voice_state.queue)}** songs.')

    @commands.command(name='clear', aliases=['c'])
    async def _clear(self, ctx: commands.Context, *, args: str = ''):
        ctx.voice_state.queue = []
        ctx.voice_state.previous = []
        await ctx.message.add_reaction('🐸')

    @commands.command(name='nowplayling', aliases=['np'])
    async def _nowplayling(self, ctx: commands.Context, *, args: str = ''):
        if ctx.voice_state.current_song:
            await ctx.send(embed=ctx.voice_state.current_song.create_embed())
        else:
            await ctx.send('Only counting flies 🐸')

    @commands.command(name='grab', aliases=['yoink'])
    async def _grab(self, ctx: commands.Context, *, args: str = ''):
        channel = await ctx.author.create_dm()
        if ctx.voice_state.current_song:
            await channel.send(embed=ctx.voice_state.current_song.create_embed())
        else:
            await channel.send('Only counting flies 🐸')

    @commands.command(name='queue', aliases=['q', 'pl'])
    async def _queue(self, ctx, page: int = 1, page_size: int = 10):
        state = self.bot.voice_states.get(ctx.guild.id)
        if state:
            message = await ctx.send(embed=state.get_queue_embed(page, page_size))
            self.bot.dispatch('new_reaction_message', state, message)
        else:
            await ctx.send('Add some songs to see your playlist.')

    @commands.command(name='loadplaylist', aliases=['lp'])
    async def _loadplaylist(self, ctx: commands.Context, *, playlist_name: str):
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)
        async with ctx.typing():
            # Search own playlists
            self.bot.c.execute(
                f"SELECT PlaylistID FROM playlists WHERE PlaylistName LIKE '%{playlist_name}%' AND CreatorID = '{ctx.author.id}'")
            playlist_id = self.bot.c.fetchone()
            # If playlist not found in own playlists search for guilds playlists
            if not playlist_id:
                self.bot.c.execute(f"SELECT PlaylistID FROM playlistsConnection WHERE GuildID = '{ctx.guild.id}'")
                ids = self.bot.c.fetchall()
                for id in ids:
                    if id:
                        self.bot.c.execute(
                            f"SELECT PlaylistID FROM playlists WHERE PlaylistName LIKE '%{playlist_name}%' AND PlaylistID = {id[0]}")
                        playlist_id = self.bot.c.fetchone()
                        if playlist_id and playlist_id[0]:
                            break

            if playlist_id:
                ctx.voice_state.load_playlist(ctx.author, playlist_id[0])
                await ctx.message.add_reaction('🐸')
            else:
                await ctx.send('Couldn\'t find your playlist. Make sure you spelled the name right 🐸')

    @commands.command(name='saveplaylist', aliases=['sp'])
    async def _saveplaylist(self, ctx: commands.Context, *, playlist_name: str):
        async with ctx.typing():
            self.bot.c.execute(
                f"SELECT PlaylistID FROM playlists WHERE PlaylistName = '{playlist_name}' AND CreatorID = '{ctx.author.id}'")
            playlist_id = self.bot.c.fetchone()
            if playlist_id:
                await ctx.send(f'You already have a playlist named **´{playlist_name}´**')
            else:
                with self.bot.conn:
                    self.bot.c.execute(
                        f"INSERT INTO playlists (PlaylistName, CreatorID) VALUES ('{playlist_name}', '{ctx.author.id}')")
                self.bot.c.execute(
                    f"SELECT PlaylistID FROM playlists WHERE PlaylistName = '{playlist_name}' AND CreatorID = '{ctx.author.id}'")
                playlist_id = self.bot.c.fetchone()[0]
                with self.bot.conn:
                    self.bot.c.execute(
                        f"INSERT INTO playlistsConnection (PlaylistID, GuildID) VALUES ({playlist_id}, '{ctx.guild.id}')")
                ctx.voice_state.save_playlist(playlist_id)
                await ctx.send(f'Successfully saved the current playlist as **`{playlist_name}`**')

    @commands.command(name='allplaylists', aliases=['ap'])
    async def _allplaylists(self, ctx: commands.Context, *, args: str = ''):
        playlists = '\u200b'
        user_playlists = ''
        self.bot.c.execute(
            f"SELECT PlaylistID, PlaylistName FROM playlists WHERE CreatorID = '{ctx.author.id}'")
        for playlist in self.bot.c.fetchall():
            user_playlists += f'- **`{playlist[1]}`**\n'
        if user_playlists:
            playlists += '\n**`Your playlists:`**\n' + user_playlists

        guild_playlists = ''
        self.bot.c.execute(f"SELECT PlaylistID FROM playlistsConnection WHERE GuildID = '{ctx.guild.id}'")
        for id in self.bot.c.fetchall():
            if id[0]:
                self.bot.c.execute(f"SELECT PlaylistName, CreatorID FROM playlists WHERE PlaylistID = {id[0]}")
                playlist = self.bot.c.fetchone()
                if playlists and playlists.find(playlist[0]) == -1:
                    guild_playlists += f'**`{playlist[0]}`** by '
                    creator = self.bot.get_user(int(playlist[1]))
                    if creator:
                        guild_playlists += f'{creator.name}#{creator.discriminator}\n'
                    else:
                        guild_playlists += 'unknown\n'

        if guild_playlists:
            playlists += '\n**`Guild playlists:`**\n' + guild_playlists

        embed = discord.Embed(title=':notepad_spiral: Playlists:',
                              description=playlists,
                              inline=False,
                              colour=discord.Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        await ctx.send(embed=embed)

    @commands.command(name='deletePlaylist', aliases=['dp', 'rmp'])
    async def _deletePlaylist(self, ctx, *, playlist_name):
        self.bot.c.execute(
            f"SELECT PlaylistID FROM playlists WHERE PlaylistName = '{playlist_name}' AND CreatorID = '{ctx.author.id}'")
        playlist_id = self.bot.c.fetchone()
        if playlist_id:
            if os.path.isfile(f"data/playlists/{playlist_id[0]}.p"):
                os.remove(f"data/playlists/{playlist_id[0]}.p")
            with self.bot.conn:
                self.bot.c.execute(f"DELETE FROM playlists WHERE PlaylistID = {playlist_id[0]}")
                self.bot.c.execute(f"DELETE FROM playlistsConnection WHERE PlaylistID = {playlist_id[0]}")
            await ctx.send(f'Successfully deleted **`{playlist_name}`**')
        else:
            await ctx.send('Couldn\'t find your playlist. Make sure you spelled the name right 🐸')

    @commands.command(name='guildaddplaylist', aliases=['gap'])
    async def _guildaddplaylist(self, ctx, *, playlist_name):
        self.bot.c.execute(
            f"SELECT PlaylistID FROM playlists WHERE PlaylistName LIKE '%{playlist_name}%' AND CreatorID = '{ctx.author.id}'")
        playlist_id = self.bot.c.fetchone()
        if playlist_id:
            self.bot.c.execute(
                f"SELECT PlaylistID FROM playlistsConnection WHERE PlaylistID = {playlist_id[0]} AND GuildID = '{ctx.guild.id}'")

            if not self.bot.c.fetchone():
                with self.bot.conn:
                    self.bot.c.execute(
                        f"INSERT INTO playlistsConnection (PlaylistID, GuildID) VALUES ({playlist_id[0]}, '{ctx.guild.id}')")
                await ctx.send(f'Added **´{playlist_name}´** to this guild.')
            else:
                await ctx.send(f'Playlist is already connected to this guild.')
        else:
            await ctx.send('Couldn\'t find your playlist. Make sure you spelled the name right 🐸')

    @commands.command(name='guildremoveplaylist', aliases=['grp'])
    async def _guildremoveplaylist(self, ctx, *, playlist_name):
        self.bot.c.execute(
            f"SELECT PlaylistID FROM playlists WHERE PlaylistName LIKE '%{playlist_name}%' AND CreatorID = '{ctx.author.id}'")
        playlist_id = self.bot.c.fetchone()
        if playlist_id:
            with self.bot.conn:
                self.bot.c.execute(
                    f"DELETE FROM playlistsConnection WHERE PlaylistID = {playlist_id[0]} and GuildID = '{ctx.guild.id}'")
            await ctx.send(f'Removed {playlist_name} from this guild.')
        else:
            await ctx.send('Couldn\'t find your playlist. Make sure you spelled the name right 🐸')

    @commands.command(name='ping')
    async def _ping(self, ctx: commands.Context, *, args: str = ''):
        embed = discord.Embed(title='Latency',
                              description='‎‎\u200b',
                              inline=False,
                              colour=discord.Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        embed.add_field(name='Client latency:', value=f' **`{round(self.bot.latency*1000)}ms`**', inline=False)
        if ctx.guild and ctx.voice_state.voice:
            latency = ctx.voice_client.latency*1000
            avg_latency = ctx.voice_client.average_latency*1000
            if latency != float('inf'):
                embed.add_field(
                    name='Voice client latency:',
                    value=f' **`{round(latency)}ms`**',
                    inline=False)
            if avg_latency != float('inf'):
                embed.add_field(
                    name=f'Average voice client latency:',
                    value=f' **`{round(avg_latency)}ms`**',
                    inline=False)
        await ctx.send(embed=embed)

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

    # Events

    @commands.Cog.listener()
    async def on_playing_song(self, voiceState: VoiceState):
        if voiceState.music_channel_id:
            channel = self.bot.get_channel(voiceState.music_channel_id)
            if channel and channel.guild and channel.type == discord.ChannelType.text:
                embed = voiceState.current_song.create_embed()
                if len(voiceState.queue) and not voiceState._loop_song:
                    song = voiceState.queue[0]
                    embed.add_field(name='‎‎\u200b',
                                    value=f'Next: [{song.title}]({song.url})',
                                    inline=False)
                message = await channel.send(embed=embed)
                self.bot.dispatch('new_reaction_message', voiceState, message)

    @commands.Cog.listener()
    async def on_new_reaction_message(self, voiceState: VoiceState, message: discord.Message):
        if voiceState.react_message_id:
            _message = await self.bot.get_channel(voiceState.react_message_channel_id).fetch_message(voiceState.react_message_id)
            await _message.clear_reactions()
        await message.add_reaction('⏮️')
        await message.add_reaction('⏯️')
        await message.add_reaction('⏭️')
        await message.add_reaction('🔀')
        await message.add_reaction('🔢')
        await message.add_reaction('❌')

        voiceState.react_message_id = message.id
        voiceState.react_message_channel_id = message.channel.id

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot or not user.guild:
            return
        state = self.bot.voice_states.get(user.guild.id)

        if state and state.react_message_id == reaction.message.id:
            await reaction.message.remove_reaction(reaction.emoji, user)
            self.bot.c.execute(f"SELECT ReqRole FROM guilds WHERE GuildID = '{user.guild.id}'")
            reqRole = self.bot.c.fetchone()
            if reqRole and reqRole[0] and user.guild.get_role(reqRole[0]) not in user.roles:
                return

            if reaction.emoji == '⏯️':
                if state.is_playing and state.voice.is_playing():
                    state.voice.pause()
                elif state.is_playing and state.voice.is_paused():
                    state.voice.resume()
            elif reaction.emoji == '⏭️':
                state.skip()
            elif reaction.emoji == '⏮️':
                state.play_previous()
            elif reaction.emoji == '🔀':
                state.shuffle()
            elif reaction.emoji == '🔢':
                message = await reaction.message.channel.send(embed=state.get_queue_embed())
                self.bot.dispatch('new_reaction_message', state, message)
            elif reaction.emoji == '❌':
                await reaction.message.clear_reactions()
                if state.voice:
                    await state.stop()
                del self.bot.voice_states[user.guild.id]
