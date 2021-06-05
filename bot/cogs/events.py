import math

from bot.classes.entry import Active, Afk, saveMessage
from bot.classes.voiceClient import VoiceClient
from discord import Colour, Embed
from discord.ext import commands


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_playing_song(self, guildId, SpamChannelId, currentSong):
        if not guildId in self.bot.voiceClients:
            return
        if guildId in self.bot.voiceClients:
            songInfo = currentSong.getInfo()
            embed = (Embed(title=':musical_note: Now playing:',
                           description=f'[{songInfo["title"]}](http://www.youtube.com/watch?v={songInfo["id"]})',
                           color=Colour.blurple())
                     .add_field(name='Requested by', value=songInfo['requester'])
                     .add_field(name='Creator', value=songInfo['creator'])
                     .set_thumbnail(url=songInfo['thumbnailUrl']))
            if self.bot.voiceClients[guildId].queue:
                nextSongInfo = self.bot.voiceClients[guildId].queue[0].getInfo()
                if nextSongInfo:
                    embed.add_field(
                        name='‎‎\u200b',
                        value=f'Next: {nextSongInfo["title"]}',
                        inline=False)
            message = await self.bot.client.get_channel(SpamChannelId).send(embed=embed)
            self.bot.client.dispatch('new_reaction_message', message)

    @commands.Cog.listener()
    async def on_new_reaction_message(self, message):
        if message.guild and message.guild.id in self.bot.voiceClients:
            VoiceClient = self.bot.voiceClients[message.guild.id]
            try:
                if VoiceClient.reactMessageId:
                    _message = await self.bot.client.get_channel(VoiceClient.reactMessageChannelId).fetch_message(VoiceClient.reactMessageId)
                    await _message.clear_reactions()
                await message.add_reaction('⏮️')
                await message.add_reaction('⏯️')
                await message.add_reaction('⏭️')
                await message.add_reaction('🔀')
                await message.add_reaction('🔢')
                await message.add_reaction('❌')
            except Exception:
                pass
            VoiceClient.reactMessageId = message.id
            VoiceClient.reactMessageChannelId = message.channel.id

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot or not user.guild:
            return
        if user.guild.id in self.bot.voiceClients:
            VoiceClient = self.bot.voiceClients[user.guild.id]
            if VoiceClient.reactMessageId == reaction.message.id:
                await reaction.message.remove_reaction(reaction.emoji, user)
                self.bot.c.execute(f"SELECT ReqRole FROM guilds WHERE GuildID = '{user.guild.id}'")
                reqRole = self.bot.c.fetchone()
                if reqRole and reqRole[0] and not (user.guild.get_role(reqRole[0]) in user.roles):
                    return
                if reaction.emoji == '⏯️':
                    if VoiceClient.voiceClient.is_playing():
                        VoiceClient.pause()
                    elif VoiceClient.voiceClient.is_paused():
                        VoiceClient.resume()
                elif reaction.emoji == '⏭️':
                    VoiceClient.nextTrack()
                elif reaction.emoji == '⏮️':
                    VoiceClient.previousTrack()
                elif reaction.emoji == '🔀':
                    VoiceClient.shuffle()
                elif reaction.emoji == '🔢':
                    pageSize = 10
                    page = 1
                    pages = math.ceil(len(self.bot.voiceClients[user.guild.id].queue)/pageSize)
                    start = (page-1) * pageSize
                    end = start + pageSize

                    embed = Embed(title=':scroll: Current Queue:',
                                        description='\u200b',
                                        color=Colour.blurple())
                    embed.set_thumbnail(url=self.bot.logoUrl)

                    if self.bot.voiceClients[user.guild.id].currentSong:
                        songInfo = self.bot.voiceClients[user.guild.id].currentSong.getInfo()
                        embed.add_field(name='Now playing:',
                                        value=f'[{songInfo["title"]}](http://www.youtube.com/watch?v={songInfo["id"]})',
                                        inline=False)

                    for i, song in enumerate(self.bot.voiceClients[user.guild.id].queue[start:end], start=start):
                        songInfo = song.getInfo()
                        if songInfo:
                            embed.add_field(name=f'**`{i+1}.`** {songInfo["title"]}',
                                            value=f'By {songInfo["creator"]}',
                                            inline=False)

                    if self.bot.voiceClients[user.guild.id].queue:
                        embed.add_field(name='\u200b',
                                        value=f'Page {page} of {pages}',
                                        inline=False)
                    else:
                        embed.add_field(name='Soo empty',
                                        value='\u200b')
                    message = await reaction.message.channel.send(embed=embed)
                    self.bot.client.dispatch('new_reaction_message', message)
                elif reaction.emoji == '❌':
                    await reaction.message.clear_reactions()
                    await VoiceClient.voiceClient.disconnect()
                    if user.guild.id in self.bot.voiceClients:
                        self.bot.voiceClients.pop(user.guild.id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if (after.afk or after.deaf or after.mute or after.self_deaf or after.self_mute) and after.channel:
            if not member.id in self.bot.usersAfk:
                self.bot.usersAfk[member.id] = Afk(member.id, after.channel.id, member.guild.id)
            if member.id in self.bot.usersActive:
                self.bot.usersActive[member.id].save(self.bot.conn, self.bot.c)
                self.bot.usersActive.pop(member.id)
        elif after.channel:
            if not member.id in self.bot.usersActive:
                self.bot.usersActive[member.id] = Active(member.id, after.channel.id, member.guild.id)
            if member.id in self.bot.usersAfk:
                self.bot.usersAfk[member.id].save(self.bot.conn, self.bot.c)
                self.bot.usersAfk.pop(member.id)
        elif not after.channel:
            if member.id in self.bot.usersAfk:
                self.bot.usersAfk[member.id].save(self.bot.conn, self.bot.c)
                self.bot.usersAfk.pop(member.id)
            elif member.id in self.bot.usersActive:
                self.bot.usersActive[member.id].save(self.bot.conn, self.bot.c)
                self.bot.usersActive.pop(member.id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # add the user to the data base if he is new
        self.bot.c.execute(f"SELECT UserID FROM users WHERE UserID = '{member.id}'")
        if not self.bot.c.fetchone():
            with self.bot.conn:
                self.bot.c.execute(f"INSERT INTO users (UserID) VALUES ('{member.id}')")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # add the guild to the database if it is new
        self.bot.logger.info(f'NEW GUILD - {guild.name} - {guild.id} - Members: {guild.member_count}')
        self.bot.c.execute(f"SELECT GuildID FROM guilds WHERE GuildID = '{guild.id}'")
        if not self.bot.c.fetchone():
            with self.bot.conn:
                self.bot.c.execute(f"INSERT INTO guilds (GuildID) VALUES ('{guild.id}')")
        # Check for new users
        for member in guild.members:
            self.bot.c.execute(f"SELECT UserID FROM users WHERE UserID = '{member.id}'")
            if not self.bot.c.fetchone():
                with self.bot.conn:
                    self.bot.c.execute(f"INSERT INTO users (UserID) VALUES ('{member.id}')")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        pass

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        self.bot.commandCounter += 1

    @commands.Cog.listener()
    async def on_message(self, message):
        saveMessage(message.author.id, message.channel.id, message.guild, self.bot.conn, self.bot.c)
        if not message.author.bot and message.content.find(f'<@!{self.bot.client.user.id}>') != -1:
            if message.guild:
                self.bot.c.execute(f"SELECT Prefix FROM guilds WHERE GuildID = '{message.guild.id}'")
                await message.channel.send(f'My current prefix is **`{self.bot.c.fetchone()[0]}`**')
            else:
                await message.channel.send(f'My current prefix is **`!`**')
