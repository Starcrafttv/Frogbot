import nextcord
from src.music.voicestate import VoiceState
from src.bot.bot import Bot
import requests
from nextcord import Embed, Colour, Message, Interaction, Button
from src.music.sec_to_time import sec_to_time


class MenuButtons(nextcord.ui.View):
    def __init__(self, bot: Bot, voice_state: VoiceState):
        self.bot = bot
        self.voice_state = voice_state
        super().__init__(timeout=None)

    def user_has_permissions(self, user) -> bool:
        response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                params={'id': user.guild.id}, headers=self.bot.header).json()
        if response.get('items') and response['items'][0]['musicRoleId'] and user.guild.get_role(
                response['items'][0]['musicRoleId']) not in user.roles:
            return False

        return True

    @nextcord.ui.button(label="", emoji="⏮️", style=nextcord.ButtonStyle.primary)
    async def previous_button(self, button: Button, interaction: Interaction):
        if interaction.user.bot or not interaction.user.guild:
            return
        elif self.user_has_permissions(interaction.user):
            await self.voice_state.play_previous()
        else:
            await interaction.response.send_messaeg("You don't have permissions to interact with the music queue.",
                                                    ephemeral=True)

    @nextcord.ui.button(label="", emoji="▶️", style=nextcord.ButtonStyle.primary)
    async def play_pause_button(self, button: Button, interaction: Interaction):
        if interaction.user.bot or not interaction.user.guild:
            return
        elif self.user_has_permissions(interaction.user):
            if self.voice_state.is_playing and self.voice_state.voice.is_playing():
                self.voice_state.voice.pause()
            elif self.voice_state.is_playing and self.voice_state.voice.is_paused():
                self.voice_state.voice.resume()
        else:
            await interaction.response.send_messaeg("You don't have permissions to pause this bot.",
                                                    ephemeral=True)

    @nextcord.ui.button(label="", emoji="⏭️", style=nextcord.ButtonStyle.primary)
    async def next_button(self, button: Button, interaction: Interaction):
        if interaction.user.bot or not interaction.user.guild:
            return
        elif self.user_has_permissions(interaction.user):
            await self.voice_state.skip()
        else:
            await interaction.response.send_messaeg("You don't have permissions to interact with the music queue.",
                                                    ephemeral=True)

    @nextcord.ui.button(label="", emoji="🔢", style=nextcord.ButtonStyle.primary)
    async def queue_button(self, button: Button, interaction: Interaction):
        message = await interaction.message.channel.send(embed=await self.voice_state.get_queue_embed())
        self.bot.dispatch('new_reaction_message', self.voice_state, message)

    @nextcord.ui.button(label="", emoji="❌", style=nextcord.ButtonStyle.grey)
    async def disconnect(self, button: Button, interaction: Interaction):
        if interaction.user.bot or not interaction.user.guild:
            return
        elif self.user_has_permissions(interaction.user):
            if self.voice_state.voice:
                await self.voice_state.stop()
            if interaction.user.guild.id in self.bot.voice_states:
                self.bot.voice_states.pop(interaction.user.guild.id)
        else:
            await interaction.response.send_messaeg("You don't have permissions to disconnect the bot.",
                                                    ephemeral=True)


class FindMenuButtons(nextcord.ui.View):
    def __init__(self, bot: Bot, voice_state: VoiceState, videos):
        self.bot = bot
        self.voice_state = voice_state
        self.videos = videos
        super().__init__(timeout=None)

    def user_has_permissions(self, user) -> bool:
        if not user.guild and user.guild.id != self.voice_state.guild_id and not user.voice:
            return False
        response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                params={'id': user.guild.id}, headers=self.bot.header).json()
        if response.get('items') and response['items'][0]['musicRoleId'] and user.guild.get_role(
                response['items'][0]['musicRoleId']) not in user.roles:
            return False

        return True

    async def play_video(self, position: int, user, message: Message):
        destination = user.voice.channel
        if self.voice_state and self.voice_state.voice:
            await self.voice_state.voice.move_to(destination)
        else:
            state = VoiceState(self.bot, user.guild.id)
            state.voice = await destination.connect()
            self.bot.voice_states[user.guild.id] = state

        song = self.videos[position]
        song.requester_name = f'{user.name}#{user.discriminator}'
        song.requester_id = user.id

        position = self.voice_state.queue.get_len()
        time_until_playing = sum(song.duration for song in self.voice_state.queue.get())

        self.voice_state.queue.put([song])

        embed = Embed(
            title=f'Added song to queue at position {position + 1}:',
            description=f'[{song.title}]({song.url})\nCreator: {song.channel_title}, Duration: {song.duration_str}',
            colour=Colour.blue())

        if time_until_playing > 0:
            embed.set_footer(text=f'Time until playing: {sec_to_time(time_until_playing)}')

        embed.set_thumbnail(url=self.bot.logo_url)

        await message.channel.send(embed=embed)
        await message.edit(view=None)

    @nextcord.ui.button(label="1", style=nextcord.ButtonStyle.primary)
    async def first_element_button(self, button: Button, interaction: Interaction):
        if self.user_has_permissions(interaction.user):
            await self.play_video(0, interaction.user, interaction.message)
        else:
            await interaction.response.send_messaeg("You don't have permissions to interact with the music queue.",
                                                    ephemeral=True)

    @nextcord.ui.button(label="2", style=nextcord.ButtonStyle.primary)
    async def second_element_button(self, button: Button, interaction: Interaction):
        if self.user_has_permissions(interaction.user):
            await self.play_video(1, interaction.user, interaction.message)
        else:
            await interaction.response.send_messaeg("You don't have permissions to interact with the music queue.",
                                                    ephemeral=True)

    @nextcord.ui.button(label="3", style=nextcord.ButtonStyle.primary)
    async def third_element_button(self, button: Button, interaction: Interaction):
        if self.user_has_permissions(interaction.user):
            await self.play_video(2, interaction.user, interaction.message)
        else:
            await interaction.response.send_messaeg("You don't have permissions to interact with the music queue.",
                                                    ephemeral=True)

    @nextcord.ui.button(label="4", style=nextcord.ButtonStyle.primary)
    async def fourth_element_button(self, button: Button, interaction: Interaction):
        if self.user_has_permissions(interaction.user):
            await self.play_video(3, interaction.user, interaction.message)
        else:
            await interaction.response.send_messaeg("You don't have permissions to interact with the music queue.",
                                                    ephemeral=True)

    @nextcord.ui.button(label="5", style=nextcord.ButtonStyle.primary)
    async def fifth_element_button(self, button: Button, interaction: Interaction):
        if self.user_has_permissions(interaction.user):
            await self.play_video(4, interaction.user, interaction.message)
        else:
            await interaction.response.send_messaeg("You don't have permissions to interact with the music queue.",
                                                    ephemeral=True)
