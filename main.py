from time import time

from discord.ext import commands

from bot.classes.bot import Bot
from bot.cogs.__cogs__ import __cogs__

bot = Bot()


def main():
    bot.start()


@bot.client.event
async def on_ready():
    bot.loadNew()
    for extension in __cogs__:
        bot.loadCog(extension)
    await bot.setStatus('s', 'with frogs')
    bot.logger.info(f"Startup: {round(time() - bot.startTime, 3)} ID={bot.client.user.id}, NAME='{bot.client.user}'")
    print(f'{bot.client.user}, {round(time() - bot.startTime, 3)}, is ready to go')


@bot.client.command(name='load', hidden=True)
@commands.is_owner()
async def _cog_load(ctx, *, cog: str):
    # Command which Loads a Module.
    response = bot.loadCog(cog)
    if response:
        await ctx.send(f'**`ERROR:`** {type(response).__name__} - {response}')
    else:
        await ctx.send('**`SUCCESS`**')


@bot.client.command(name='unload', hidden=True)
@commands.is_owner()
async def _cog_unload(ctx, *, cog: str):
    # Command which Loads a Module.
    response = bot.removeCog(cog)
    if response:
        await ctx.send(f'**`ERROR:`** {type(response).__name__} - {response}')
    else:
        await ctx.send('**`SUCCESS`**')


@bot.client.command(name='reload', hidden=True)
@commands.is_owner()
async def _cog_reload(ctx, *, cog: str):
    # Command which Loads a Module.
    response = bot.removeCog(cog)
    if response:
        await ctx.send(f'**`ERROR:`** {type(response).__name__} - {response}')
    else:
        response = bot.loadCog(cog)
        if response:
            await ctx.send(f'**`ERROR:`** {type(response).__name__} - {response}')
        else:
            await ctx.send('**`SUCCESS`**')


@bot.client.command(name='shutdown', aliases=['bot'], hidden=True)
@commands.is_owner()
async def _bot(ctx, arg=''):
    # Turn off the bot
    if arg.lower() == 'off':
        print('Shutdown initiated')
        bot.logger.critical(f"'{ctx.author.name}#{ctx.author.discriminator}' initiated shutdown")
        await ctx.send('Going to sleep :zzz:')
        # Unload all loaded cogs
        for extension in bot.loadedCogs:
            response = bot.removeCog(extension)
            if response:
                bot.logger.exception(f'_bot - {response}')
        await bot.logout()


if __name__ == '__main__':
    main()
