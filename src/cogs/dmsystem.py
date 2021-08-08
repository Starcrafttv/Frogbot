import requests
from discord import Message
from discord.ext import commands
from src.bot.bot import Bot


class Dmsystem(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        if not message.guild and message.content[0] != '!':
            response = requests.get(f'{self.bot.base_api_url}discord/direct/message/',
                                    params={'userId': message.author.id}, headers=self.bot.header).json()
            if response.get('items'):
                channel = await self.bot.fetch_channel(response['items'][0]['channelId'])
                await channel.send(f'{message.author.name}: {message.content}')
            else:
                channel = await self.bot.fetch_channel(self.bot.support_log_channel_id)
                new_channel = await channel.guild.create_text_channel(f'ticket-{message.author.name}-{message.author.id}')
                category = self.bot.get_channel(self.bot.support_category_id)
                await new_channel.edit(category=category)
                await new_channel.set_permissions(channel.guild.default_role,
                                                  read_messages=False,
                                                  send_messages=False)
                await new_channel.set_permissions(channel.guild.get_role(self.bot.support_role_id),
                                                  send_messages=True,
                                                  read_messages=True,
                                                  embed_links=True,
                                                  attach_files=True,
                                                  read_message_history=True,
                                                  add_reactions=True)
                await new_channel.send(f'{message.author.name}: {message.content}')
                request = {
                    'userId': message.author.id,
                    'channelId': new_channel.id
                }
                requests.put(f'{self.bot.base_api_url}discord/direct/message/', params=request, headers=self.bot.header)

                await message.reply('Thank you for your message! Our mod team will reply to you as soon as possible.', mention_author=False)
            return
        response = requests.get(f'{self.bot.base_api_url}discord/direct/message/',
                                params={'channelId': message.channel.id}, headers=self.bot.header).json()
        if response.get('items'):
            user_id = response['items'][0]['userId']
            response = requests.get(f'{self.bot.base_api_url}discord/guild/',
                                    params={'id': message.guild.id}, headers=self.bot.header).json()
            if response.get('items') and response['items'][0]['prefix'] != message.content[0]:
                await self.bot.get_user(int(user_id[0][0])).send(message.content)
                await message.add_reaction('✅')

    @ commands.command(name='close', hidden=True)
    @ commands.is_owner()
    async def close(self, ctx: commands.Context):
        response = requests.get(f'{self.bot.base_api_url}discord/direct/message/',
                                params={'channelId': ctx.channel.id}, headers=self.bot.header).json()
        if response.get('items'):
            requests.delete(f'{self.bot.base_api_url}discord/direct/message/',
                            params={'userId': response['items'][0]['userId']},
                            headers=self.bot.header).json()
            log = f'User-ID:\'{response["items"][0]["userId"]}\'\n'
            messages = await ctx.channel.history(limit=200).flatten()
            for message in reversed(messages):
                log = f'{log}{message.created_at.strftime("%d.%m.%y %H:%M")} | {message.author.name}: {message.content}\n'
            log = f'```{log}```'
            logChannel = ctx.channel.guild.get_channel(self.bot.support_log_channel_id)
            await logChannel.send(log)
            await ctx.channel.delete()

    @ commands.command(name='open Dms', aliases=['od'], hidden=True)
    @ commands.is_owner()
    async def openDms(self, ctx: commands.Context):
        response = requests.get(f'{self.bot.base_api_url}discord/direct/message/',
                                params={}, headers=self.bot.header).json()

        message = ''
        for dm in response.get('items', []):
            message = f'{message}User ID:{dm["userId"]}, Channel ID:{dm["channelId"]}\n'
        if not message:
            message = 'No open tickets'
        await ctx.send(f'```{message}```')
