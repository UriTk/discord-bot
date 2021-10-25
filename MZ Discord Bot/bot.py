import discord
from discord.ext import commands
import asyncio
import callofduty
from callofduty import Mode, Platform, Title
import urllib.parse
from constants import TOKEN, PREFIX, EMAIL, PASS, ROLE0, ROLE1, ROLE2, ROLE3, ROLE4, ROLE5


client = commands.Bot(PREFIX)


@client.event  # When bot launches
async def on_ready():
    print("\nModern Warfare Discord Bot Startup\nLogged in as: {}".format(client.user.name))
    # This next line is optional. It changes the bot's "Status". I generally like to use it to tell users how to use the bot. If you don't want it, you can simply delete it. It won't mess anything up.
    await client.change_presence(activity=discord.Game(name=f"{PREFIX}rankme"))


@client.command()  # If you want to change what the user need sto input to trigger the command, simply change the "rankme" part to whatever you want the command to be.
async def rankme(ctx, platform, *, name=''):
    if name == '':  # If the player didn't input a name or a platform, tell them how to use the command properly.
        await ctx.message.channel.send(
            f"Not enough arguments. \nPlease use the command like this: {PREFIX}rankme \"XB/PS/PC (User ID).\ni.e.: {PREFIX}rankme PC Uri#11398")
        return
    if platform.lower() not in ("xb", "ps", "pc"):
        print("test")
        await ctx.message.channel.send(
            f"Did you input the platform correctly? \nPlease use the command like this: {PREFIX}rankme \"XB/PS/PC (User ID).\nexample: {PREFIX}rankme PC Uri#11398")
        return

    notification = await ctx.message.channel.send(f"Searching for user...")

    # This is where you need to put in your Activision login info, which acts as an access to the activision API.
    client = await callofduty.Login(EMAIL, PASS)

    if platform.lower() == "pc":
        results = await client.SearchPlayers(Platform.BattleNet, name, limit=3)
    elif platform.lower() == "ps":
        results = await client.SearchPlayers(Platform.PlayStation, name, limit=3)
    elif platform.lower() == "xb":
        results = await client.SearchPlayers(Platform.Xbox, name, limit=3)

    # Try Except statement in case it doesn't find any users with said name.
    try:
        player = results[0]
    except IndexError:
        await ctx.message.channel.send(f"No users with the name {name} found.")
        await notification.delete()  # Deletes the original "Searching for user" message.
        return

    # Grab the user's Modern Warfare profile.
    try:
        profile = await player.profile(Title.ModernWarfare, Mode.Warzone)
    except:
        await ctx.message.channel.send(f"Failed to load your stats. \nMake sure your settings are set to \"All\" in https://profile.callofduty.com/cod/profile")
        await notification.delete()  # Deletes the original "Searching for user" message.
        return

    # Try Except statement in case the user doesn't have any stats on Warzone.
    try:
        kd = profile["lifetime"]["mode"]["br"]["properties"]["kdRatio"]
    except TypeError:
        await ctx.message.channel.send("This user has not played the game.")
        await notification.delete()  # Deletes the original "Searching for user" message.
        return

    # Grabs the roles. If you ever change the name of the roles, you'll have to change the part of these lines that's in quotes. i.e. name="+6 KD" to name="6 PLUS KD".
    KD5 = discord.utils.get(ctx.guild.roles, name=ROLE5)
    KD4 = discord.utils.get(ctx.guild.roles, name=ROLE4)
    KD3 = discord.utils.get(ctx.guild.roles, name=ROLE3)
    KD2 = discord.utils.get(ctx.guild.roles, name=ROLE2)
    KD1 = discord.utils.get(ctx.guild.roles, name=ROLE1)
    KD0 = discord.utils.get(ctx.guild.roles, name=ROLE0)

    # Another if elif chain. I'd wish Python had "switch" cases. This part of the code assigns the user their respective role, and removes all others to avoid multiple roles.
    if kd >= 4:
        await ctx.author.add_roles(KD5)
        await ctx.author.remove_roles(KD4, KD3, KD2, KD1, KD0)
    elif kd >= 3:
        await ctx.author.add_roles(KD4)
        await ctx.author.remove_roles(KD5, KD3, KD2, KD1, KD0)
    elif kd >= 2:
        await ctx.author.add_roles(KD3)
        await ctx.author.remove_roles(KD5, KD4, KD2, KD1, KD0)
    elif kd >= 1.5:
        await ctx.author.add_roles(KD2)
        await ctx.author.remove_roles(KD5, KD4, KD3, KD1, KD0)
    elif kd >= 1:
        await ctx.author.add_roles(KD1)
        await ctx.author.remove_roles(KD5, KD4, KD3, KD2, KD0)
    else:
        await ctx.author.add_roles(KD0)
        await ctx.author.remove_roles(KD5, KD4, KD3, KD2, KD1)

    await notification.delete()  # Deletes the original "Searching for user" message.
    await ctx.message.channel.send(
        f"The K/D Ratio of {player.username} is: {round(kd, 2)}, you have been assigned the respective role.")

client.run(TOKEN)  # Your Discord Bot's Token ID goes here.
