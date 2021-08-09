import requests
from discord import Guild, Member, Message, User, VoiceState
from discord.ext import commands
from src.bot.bot import Bot


class Recorder(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        for guild in self.bot.guilds:
            # Check if the guild is in the database
            request = {'id': guild.id,
                       'name': guild.name,
                       'ownerId': guild.owner_id,
                       'createdAt': guild.created_at.timestamp(),
                       'banner': guild.banner}
            requests.put(f'{self.bot.base_api_url}discord/guild/',
                         params=request, headers=self.bot.header)

            # Check for user in channels
            for channel in guild.voice_channels:
                for member in channel.members:
                    if not member.bot:
                        params = {
                            'userId': member.id,
                            'channelId': channel.id,
                            'guildId': guild.id
                        }
                        if member.voice.afk or member.voice.deaf or member.voice.mute or member.voice.self_deaf or member.voice.self_mute:
                            requests.put(f'{self.bot.base_api_url}discord/afk/', params=params, headers=self.bot.header)
                        else:
                            requests.put(f'{self.bot.base_api_url}discord/active/',
                                         params=params, headers=self.bot.header)
        # Go through all available user and check if they are in the database
        for user in self.bot.users:
            requests.put(f'{self.bot.base_api_url}discord/user/',
                         params={'id': user.id,
                                 'name': user.name,
                                 'discriminator': user.discriminator,
                                 'createdAt': user.created_at.timestamp(),
                                 'avatar': user.avatar,
                                 'bot': user.bot},
                         headers=self.bot.header)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if member.bot:
            return

        request = {
            'userId': member.id,
            'guildId': member.guild.id,
            'channelId': after.channel.id if after.channel else None
        }

        if after.channel:
            if after.afk or after.deaf or after.mute or after.self_deaf or after.self_mute:
                requests.put(f'{self.bot.base_api_url}discord/afk/', params=request, headers=self.bot.header)
            else:
                requests.put(f'{self.bot.base_api_url}discord/active/', params=request, headers=self.bot.header)
        else:
            requests.put(f'{self.bot.base_api_url}discord/offline/', params=request, headers=self.bot.header)

    @commands.Cog.listener()
    async def on_user_update(self, _: User, after: User):
        requests.put(f'{self.bot.base_api_url}discord/user/', params={
                     'id': after.id,
                     'name': after.name,
                     'discriminator': after.discriminator,
                     'createdAt': after.created_at.timestamp(),
                     'avatar': after.avatar,
                     'bot': after.bot},
                     headers=self.bot.header)

    @commands.Cog.listener()
    async def on_guild_update(self, before: Guild, after: Guild):
        requests.put(f'{self.bot.base_api_url}discord/guild/',
                     params={'id': after.id,
                             'name': after.name,
                             'ownerId': after.owner_id,
                             'createdAt': after.created_at.timestamp(),
                             'banner': after.banner},
                     headers=self.bot.header)

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        # add the user to the data base if he is new
        requests.put(f'{self.bot.base_api_url}discord/user/',
                     params={'id': member.id,
                             'name': member.name,
                             'discriminator': member.discriminator,
                             'createdAt': member.created_at.timestamp(),
                             'avatar': member.avatar,
                             'bot': member.bot},
                     headers=self.bot.header)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        # add the guild to the database if it is new
        self.bot.logger.info(f'NEW GUILD - {guild.name} - {guild.id} - Members: {guild.member_count}')
        requests.put(f'{self.bot.base_api_url}discord/guild/',
                     params={'id': guild.id,
                             'name': guild.name,
                             'ownerId': guild.owner_id,
                             'createdAt': guild.created_at.timestamp(),
                             'banner': guild.banner},
                     headers=self.bot.header)

        # Check for new users
        for member in guild.members:
            requests.put(f'{self.bot.base_api_url}discord/user/',
                         params={'id': member.id,
                                 'name': member.name,
                                 'discriminator': member.discriminator,
                                 'createdAt': member.created_at.timestamp(),
                                 'avatar': member.avatar,
                                 'bot': member.bot},
                         headers=self.bot.header)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        requests.put(f'{self.bot.base_api_url}discord/message/',
                     params={'id': message.id,
                             'userId': message.author.id,
                             'guildId': message.guild.id if message.guild else None,
                             'channelId': message.channel.id},
                     headers=self.bot.header)
