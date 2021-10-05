import os
from time import time

from src.bot.buttons import MenuButtons, FindMenuButtons
import requests
import src.music.search as search
from nextcord import ChannelType, Colour, Embed, Message, Reaction, Member
from nextcord.ext import commands
from src.bot.bot import Bot
from src.music.sec_to_time import sec_to_time
from src.music.song import Song
from src.music.voicestate import VoiceState


class Music(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def music_error(self, ctx: commands.Context, error: str):
        await ctx.send(error)

    def get_voice_state(self, ctx: commands.Context) -> VoiceState:
        state = self.bot.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx.guild.id)
            self.bot.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.bot.voice_states.values():
            self.bot.loop.create_task(state.stop())

    async def check(self, channel, guild, user):
        if not guild:
            await channel.send('This command can\'t be used in DM channels.')
            return False

        response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                params={'id': guild.id}, headers=self.bot.header).json()

        if response.get('items') and response['items'][0]['musicRoleId'] and guild.get_role(
                response['items'][0]['musicRoleId']) not in user.roles:
            await channel.send('You need permissions to use this command.')
            return False

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send(f'An error occurred: {error}')

    # Commands

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['dc'])
    async def _leave(self, ctx: commands.Context):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        if not ctx.voice_state.voice:
            await ctx.send('I am not connected to any voice channel right now.')
            return

        await ctx.voice_state.stop()
        if ctx.guild.id in self.bot.voice_states:
            self.bot.voice_states.pop(ctx.guild.id)

    @commands.command(name='play', aliases=['p'])
    async def _play(self, ctx: commands.Context, *, query: str = ''):
        if not await self.check(ctx.channel, ctx.guild, ctx.author) or not query:
            return

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                songs = await search.get_songs(ctx.author, query)
            except Exception as e:
                await self.music_error(
                    ctx, f'An error occurred while processing this request: {e}'
                )

            else:
                position = ctx.voice_state.queue.get_len()
                time_until_playing = sum(song.duration for song in ctx.voice_state.queue.get())
                ctx.voice_state.queue.put(songs)
                await self.play_command_message(ctx, songs, position, time_until_playing)

    @commands.command(name='playtop', aliases=['pt'])
    async def _playtop(self, ctx: commands.Context, *, query: str = ''):
        if not await self.check(ctx.channel, ctx.guild, ctx.author) or not query:
            return

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                songs = await search.get_songs(ctx.author, query)
            except Exception as e:
                await self.music_error(ctx, f'An error occurred while processing this request: {e}')
            else:
                ctx.voice_state.queue.put_first(songs)
                await self.play_command_message(ctx, songs)

    @commands.command(name='playskip', aliases=['ps'])
    async def _playskip(self, ctx: commands.Context, *, query: str = ''):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                songs = await search.get_songs(ctx.author, query)
            except Exception as e:
                await self.music_error(ctx, f'An error occurred while processing this request: {e}')
            else:
                ctx.voice_state.queue.put_first(songs)
                await ctx.voice_state.skip()
                await self.play_command_message(ctx, songs)

    async def play_command_message(self, ctx: commands.Context, songs: list[Song], position: int = 0,
                                   time_until_playing: int = 0):
        if len(songs) == 1:
            embed = Embed(
                title=f'Added song to queue at position {position + 1}',
                description=f'[{songs[0].title}]({songs[0].url})\n'
                            f'Creator: {songs[0].channel_title}, Duration: {songs[0].duration_str}',
                colour=Colour.blue())
        else:
            embed = Embed(
                title=f'Added {len(songs)} songs to queue at position {position + 1}',
                description=f'1. ‎[{songs[0].title}]({songs[0].url})\n...\n{len(songs)}. '
                            f'‎‎[{songs[-1].title}]({songs[-1].url})',
                colour=Colour.blue())

        if time_until_playing > 0:
            embed.set_footer(text=f'Time until playing: {sec_to_time(time_until_playing)}')

        embed.set_thumbnail(url=self.bot.logo_url)
        await ctx.send(embed=embed)

    @commands.command(name='skip', aliases=['s'])
    async def _skip(self, ctx: commands.Context, *, args: str = ''):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        if ctx.voice_state.voice:
            try:
                args = int(args) - 1
            except ValueError:
                args = 0

            await ctx.voice_state.skip(args)
            await ctx.message.add_reaction('🐸')

    @commands.command(name='seek', aliases=['sek'])
    async def _seek(self, ctx: commands.Context, *, args: str = '0'):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        args = args.split(':')[-3:][::-1]

        position = 0

        for i in range(len(args)):
            try:
                position += int(args[i]) * [1, 60, 3600][i]
            except ValueError:
                pass

        if ctx.voice_state and ctx.voice_state.voice and ctx.voice_state.current_song:
            if position < 0:
                position = 0
            elif position > ctx.voice_state.current_song.duration:
                await ctx.voice_state.skip()
                await ctx.message.add_reaction('🐸')
                return
            await ctx.voice_state.seek_position(position)
            await ctx.message.add_reaction('🐸')
        else:
            await ctx.send('Not playing anything currently.')

    @commands.command(name='pause', aliases=['pse'])
    async def _pause(self, ctx: commands.Context, *, args: str = ''):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('🐸')

    @commands.command(name='resume', aliases=['res'])
    async def _resume(self, ctx: commands.Context, *, args: str = ''):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('🐸')

    @commands.command(name='shuffle', aliases=['random'])
    async def _shuffle(self, ctx: commands.Context, *, args: str = ''):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        await ctx.voice_state.shuffle()
        await ctx.message.add_reaction('🐸')

    @commands.command(name='remove', aliases=['rm'])
    async def _remove(self, ctx: commands.Context, index: int = 1):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        if ctx.voice_state.queue.get_len() and 0 <= index - 1 <= ctx.voice_state.queue.get_len():
            ctx.voice_state.queue.pop(index - 1)
            await ctx.message.add_reaction('🐸')

    @commands.command(name='move', aliases=['m'])
    async def _move(self, ctx: commands.Context, from_index: int, to_index: int = 1):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        if (
                ctx.voice_state.queue.get_len()
                and 0 <= from_index - 1 <= ctx.voice_state.queue.get_len()
                and 0 <= to_index - 1 <= ctx.voice_state.queue.get_len()
        ):
            song = ctx.voice_state.queue.pop(from_index - 1)
            ctx.voice_state.queue.put_index(song, to_index - 1)
            await ctx.message.add_reaction('🐸')

    @commands.command(name='loopsong', aliases=['ls'])
    async def _loopsong(self, ctx: commands.Context, *, args: str = ''):
        if not await self.check(ctx.channel, ctx.guild, ctx.author) or not ctx.voice_state.current_song:
            return

        ctx.voice_state._loop_queue = False
        if ctx.voice_state._loop_song:
            ctx.voice_state._loop_song = False
            await ctx.send('Stopped the loop of eternity')
        else:
            ctx.voice_state._loop_song = True
            await ctx.send(f'Repeating **{ctx.voice_state.current_song.title}** for ever.')

    @commands.command(name='loopqueue', aliases=['lq'])
    async def _loopqueue(self, ctx: commands.Context, *, args: str = ''):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        ctx.voice_state._loop_song = False
        if ctx.voice_state._loop_queue:
            ctx.voice_state._loop_queue = False
            await ctx.send('Stopped the loop of eternity')
        else:
            ctx.voice_state._loop_queue = True

            await ctx.send(f'Repeating these **{ctx.voice_state.queue.get_len()}** songs.')

    @commands.command(name='clear', aliases=['c'])
    async def _clear(self, ctx: commands.Context, *, args: str = ''):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        ctx.voice_state.queue.clear()
        ctx.voice_state.previous.clear()
        await ctx.message.add_reaction('🐸')

    @commands.command(name='nowplayling', aliases=['np'])
    async def _nowplayling(self, ctx: commands.Context, *, args: str = ''):
        if ctx.voice_state.current_song:
            await ctx.send(embed=await ctx.voice_state.current_song.create_embed())
        else:
            await ctx.send('Only counting flies 🐸')

    @commands.command(name='grab', aliases=['yoink'])
    async def _grab(self, ctx: commands.Context, *, args: str = ''):
        channel = await ctx.author.create_dm()
        if ctx.voice_state.current_song:
            await channel.send(embed=await ctx.voice_state.current_song.create_embed())
        else:
            await channel.send('Only counting flies 🐸')

    @commands.command(name='queue', aliases=['q', 'pl'])
    async def _queue(self, ctx, page: int = 1, page_size: int = 10):
        state = self.bot.voice_states.get(ctx.guild.id)
        if state:
            message = await ctx.send(embed=await state.get_queue_embed(page, page_size))
            self.bot.dispatch('new_reaction_message', state, message)
        else:
            await ctx.send('Add some songs to see your playlist.')

    @commands.command(name='loadplaylist', aliases=['lp'])
    async def _loadplaylist(self, ctx: commands.Context, *, playlist_name: str):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)
        async with ctx.typing():
            # Search own playlists
            response = requests.get(f'{self.bot.base_api_url}playlist/',
                                    params={'name': playlist_name, 'userId': ctx.author.id},
                                    headers=self.bot.header).json()
            if not response.get('items'):
                for item in requests.get(
                        f'{self.bot.base_api_url}playlist/connections/', params={'guildId': ctx.guild.id},
                        headers=self.bot.header).json().get('items', []):
                    response = requests.get(f'{self.bot.base_api_url}playlist/',
                                            params={'id': item['playlistId'],
                                                    'name': playlist_name},
                                            headers=self.bot.header).json()
                    if response.get('items'):
                        break
                else:
                    await ctx.send('Couldn\'t find your playlist. Make sure you spelled the name right 🐸')
                    return
            songs = await ctx.voice_state.load_playlist(ctx.author, response['items'][0]['id'])
            position = ctx.voice_state.queue.get_len()
            time_until_playing = sum(song.duration for song in ctx.voice_state.queue.get())
            ctx.voice_state.queue.put(songs)
            await self.play_command_message(ctx, songs, position, time_until_playing)

    @commands.command(name='saveplaylist', aliases=['sp'])
    async def _saveplaylist(self, ctx: commands.Context, *, playlist_name: str):
        async with ctx.typing():
            if ctx.voice_state.current_song or ctx.voice_state.queue.get_len():

                response = requests.get(f'{self.bot.base_api_url}playlist/',
                                        params={'name': playlist_name, 'userId': ctx.author.id},
                                        headers=self.bot.header)
                if response.json()['items']:
                    await ctx.send(f'You already have a playlist named **´{playlist_name}´**')
                else:
                    response = requests.put(f'{self.bot.base_api_url}playlist/',
                                            params={'name': playlist_name, 'userId': ctx.author.id},
                                            headers=self.bot.header)
                    if response.status_code == 200:

                        playlist_id = requests.get(f'{self.bot.base_api_url}playlist/',
                                                   params={'name': playlist_name, 'userId': ctx.author.id},
                                                   headers=self.bot.header).json()['items'][0]['id']
                        requests.put(
                            f'{self.bot.base_api_url}playlist/connections/',
                            params={'playlistId': playlist_id, 'guildId': ctx.guild.id},
                            headers=self.bot.header)

                        await ctx.voice_state.save_playlist(playlist_id)
                        await ctx.send(f'Successfully saved the current playlist as **`{playlist_name}`**')
                    else:
                        await ctx.send('Something went wrong. Maybe try a different playlist name.')
            else:
                await ctx.send('No songs to save. Please add at least one song to the queue.')

    @commands.command(name='allplaylists', aliases=['ap'])
    async def _all_playlists(self, ctx: commands.Context, *, args: str = ''):
        playlists = '\u200b'
        user_playlists = ''.join(
            f'- **`{playlist["name"]}`**\n'
            for playlist in requests.get(
                f'{self.bot.base_api_url}playlist/',
                params={'userId': ctx.author.id},
                headers=self.bot.header,
            ).json().get('items', [])
        )

        if user_playlists:
            playlists += '\n**`Your playlists:`**\n' + user_playlists

        guild_playlists = ''
        for item in requests.get(
                f'{self.bot.base_api_url}playlist/connections/', params={'guildId': ctx.guild.id},
                headers=self.bot.header).json().get('items', []):
            response = requests.get(f'{self.bot.base_api_url}playlist/',
                                    params={'id': item['playlistId']},
                                    headers=self.bot.header).json()
            if response.get('items') and playlists.find(response['items'][0]['name']) == -1:
                guild_playlists += f'- **`{response["items"][0]["name"]}`** by '
                creator = self.bot.get_user(response['items'][0]['userId'])
                if creator:
                    guild_playlists += f'{creator.name}#{creator.discriminator}\n'
                else:
                    guild_playlists += 'unknown\n'
        if guild_playlists:
            playlists += '\n**`Guild playlists:`**\n' + guild_playlists

        embed = Embed(title=':notepad_spiral: Playlists:',
                      description=playlists,
                      colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        await ctx.send(embed=embed)

    @commands.command(name='deletePlaylist', aliases=['dp', 'rmp'])
    async def _delete_playlist(self, ctx, *, playlist_name):
        response = requests.get(
            f'{self.bot.base_api_url}playlist/', params={'userId': ctx.author.id},
            headers=self.bot.header).json()
        if response.get('items'):
            if os.path.isfile(f'data/playlists/{response["items"][0]["id"]}.p'):
                os.remove(f'data/playlists/{response["items"][0]["id"]}.p')
            requests.delete(f'{self.bot.base_api_url}playlist/',
                            params={'id': response['items'][0]['id']}, headers=self.bot.header)
            await ctx.send(f'Successfully deleted **{playlist_name}**')
        else:
            await ctx.send('Couldn\'t find your playlist. Make sure you spelled the name right 🐸')

    @commands.command(name='guildaddplaylist', aliases=['gap'])
    async def _guildaddplaylist(self, ctx, *, playlist_name):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        response = requests.get(f'{self.bot.base_api_url}playlist/',
                                params={'userId': ctx.author.id, 'name': playlist_name},
                                headers=self.bot.header).json()

        if response.get('items'):
            response = requests.put(
                f'{self.bot.base_api_url}playlist/connections/',
                params={'playlistId': response['items'][0]['id'],
                        'guildId': ctx.guild.id},
                headers=self.bot.header)

            if response.status_code == 200:
                await ctx.send(f'Added **{playlist_name}** to this guild.')
            else:
                await ctx.send(f'Playlist is already connected to this guild.')
        else:
            await ctx.send('Couldn\'t find your playlist. Make sure you spelled the name right 🐸')

    @commands.command(name='guildremoveplaylist', aliases=['grp'])
    async def _guildremoveplaylist(self, ctx, *, playlist_name):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        response = requests.get(f'{self.bot.base_api_url}playlist/',
                                params={'userId': ctx.author.id, 'name': playlist_name},
                                headers=self.bot.header).json()
        if response.get('items'):
            requests.delete(f'{self.bot.base_api_url}playlist/connections/',
                            params={'playlistId': response['items'][0]['id'], 'guildId': ctx.guild.id},
                            headers=self.bot.header).json()
            await ctx.send(f'Removed {playlist_name} from this guild.')
        else:
            await ctx.send('Couldn\'t find your playlist. Make sure you spelled the name right 🐸')

    @commands.command(name='ping')
    async def _ping(self, ctx: commands.Context, *, args: str = ''):
        embed = Embed(title='Latency',
                      description='‎‎\u200b',
                      colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        embed.add_field(name='Client latency:', value=f' **`{round(self.bot.latency * 1000)}ms`**', inline=False)
        if ctx.guild and ctx.voice_state.voice:
            latency = ctx.voice_client.latency * 1000
            avg_latency = ctx.voice_client.average_latency * 1000
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

    @commands.command(name='find', aliases=['search'])
    async def _find(self, ctx: commands.Context, *, args: str = ''):
        if not await self.check(ctx.channel, ctx.guild, ctx.author):
            return

        videos = await search.search_youtube_video(ctx.author, args, 5)

        embed = Embed(title=f'Results for: **`{args}`**',
                      description='‎‎\u200b',
                      colour=Colour.blue())
        embed.set_thumbnail(url=self.bot.logo_url)
        for i, video in enumerate(videos):
            embed.add_field(
                name=f'{i + 1}. {video.title}',
                value=f'Creator: {video.channel_title}, Duration: {video.duration_str}', inline=False)
        embed.set_footer(text='React to add to queue')
        message = await ctx.send(embed=embed, view=FindMenuButtons(self.bot, ctx.voice_state, videos))

    @_join.before_invoke
    @_play.before_invoke
    @_playtop.before_invoke
    @_playskip.before_invoke
    @_skip.before_invoke
    @_pause.before_invoke
    @_resume.before_invoke
    @_shuffle.before_invoke
    @_remove.before_invoke
    @_move.before_invoke
    @_loopsong.before_invoke
    @_loopqueue.before_invoke
    @_clear.before_invoke
    @_clear.before_invoke
    @_loadplaylist.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

    # Events

    @commands.Cog.listener()
    async def on_playing_song(self, voice_state: VoiceState):
        if voice_state.music_channel_id:
            channel = self.bot.get_channel(voice_state.music_channel_id)
            if channel and channel.guild and channel.type == ChannelType.text:
                embed = await voice_state.current_song.create_embed()
                if voice_state.queue.get_len() and not voice_state._loop_song:
                    song = voice_state.queue.get_first()
                    embed.add_field(name='‎‎\u200b',
                                    value=f'Next: [{song.title}]({song.url})',
                                    inline=False)
                message = await channel.send(embed=embed)
                self.bot.dispatch('new_reaction_message', voice_state, message)

    @commands.Cog.listener()
    async def on_new_reaction_message(self, voice_state: VoiceState, message: Message):
        if voice_state.react_message_id:
            old_message = await self.bot.get_channel(voice_state.react_message_channel_id).fetch_message(
                voice_state.react_message_id)
            await old_message.edit(view=None)

        await message.edit(view=MenuButtons(self.bot, voice_state))

        voice_state.react_message_id = message.id
        voice_state.react_message_channel_id = message.channel.id
