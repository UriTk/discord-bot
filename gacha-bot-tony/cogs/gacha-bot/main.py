import discord
from discord.ext import commands, tasks
import os
import json
import datetime

# import settings
from UtilityFiles.constants import TOKEN, PREFIX

bot = commands.Bot(command_prefix= PREFIX, case_insensitive=True) # initates bot and sets prefix

#TODO: add color option to config
#TODO: finish refactor
#TODO: get menus module working


@bot.event
async def on_ready():
	print('\nLogged in as:')
	print(" Username", bot.user.name)
	print(" User ID", bot.user.id)
	print("To invite the bot in your server use this link:\n https://discordapp.com/oauth2/authorize?&client_id="+str(bot.user.id)+"&scope=bot&permissions=0")
	print("Time now", str(datetime.datetime.now()))

''' # uncomment this to catch errors
@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		pass
	elif isinstance(error, commands.MissingRequiredArgument):
		await ctx.send("Command missing argument")
	elif isinstance(error, commands.BadArgument):
		await ctx.send("Invalid command argument")
	else:
		print(error, ctx)
'''

def is_allowed(ctx):  # A role/owner check for some commands

    groups = ctx.message.author.roles  # The user's roles
    admin = False
    for group in groups:  # Checks if any of the
        if group.permissions.manage_guild:
            admin = True

    if str(ctx.message.guild.owner_id) == str(ctx.message.author.id):
        admin = True
    if admin:
        return True
    return False

def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            bot.load_extension(f'cogs.{filename[:-3]}')

#@bot.command(pass_context=True, aliases=["re"])
#@commands.check(is_allowed)
#async def reload(ctx, extension=None):
#    if extension is None:
#        for filename in os.listdir('./cogs'):
#            if filename.endswith('.py') and filename != '__init__.py':
#                bot.unload_extension(f'cogs.{filename[:-3]}')
#                bot.load_extension(f'cogs.{filename[:-3]}')
#        await ctx.send("Finished reloading Cogs.")
#    else:
#        extension = extension.title()
#        bot.unload_extension(f'cogs.{extension}')
#        await ctx.send(f'Reloading cog `{extension}`')
#        bot.load_extension(f'cogs.{extension}')
#        await ctx.send(f'Finished reloading cog `{extension}`')

load_cogs()
bot.run(TOKEN) # runs bot
