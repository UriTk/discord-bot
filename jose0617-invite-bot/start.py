from datetime import datetime, timedelta
import discord
import json
from discord.ext import commands, tasks

from config import prefix, token, COLOR

client = commands.Bot(prefix)  # Sets the prefix based on what's on config.ini


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

@client.event  # When the bot first launches
async def on_ready():
    print('\nLogged in as:')
    print(" Username", client.user.name)
    print(" User ID", client.user.id)
    print("To invite the bot in your server use this link:\n https://discordapp.com/oauth2/authorize?&client_id=" + str(
        client.user.id) + "&scope=bot&permissions=0")

@client.command(pass_context=True, name="reset")
@commands.check(is_allowed)
async def reset(ctx):
    empty_inventory = {"totalinvites": 0, "tempinvites": 0, "codes": {},
                       "usersinvited": {}}  # Set an empty inventory of sorts
    data1 = {}

    for i in await ctx.guild.invites():  # For invite in the guild
        id = str(i.inviter.id)  # Gets inviter's ID

        if id not in data1:  # If the user's ID is not in data1 yet, add it with an empty inventory
            data1[id] = empty_inventory
        data1[id]["totalinvites"] += i.uses  # Adds everything we need to add to it
        data1[id]["tempinvites"] += i.uses
        data1[id]["codes"][i.code] = i.uses

    with open("user_info.json", "w") as f:  # Dump the data we have into user_info.json
        dump_data(data1, f)
    await ctx.send("Invite counters have been reset.")


@client.event
async def on_member_join(member):  # When a member joins
    with open("user_info.json", "r") as f:
        user_info = json.load(f)
    for i in member.guild.invites():
        id = str(i.inviter.id)

        if user_info[id]["tempinvites"][i.code] != i.uses:
            user_info[id]["tempinvites"] += 1
            user_info[id]["codes"][i.code] += 1
            user_info[id]["usersinvited"][member.id] = i.code
            with open("user_info.json", "w") as f:
                dump_data(user_info, f)


@client.event
async def on_member_remove(member):  # When a member exits the guild, either forcefuly or manually.
    with open("user_info.json", "r") as f:
        user_info = json.load(f)
    for i in member.guild.invites():
        id = str(i.inviter.id)

        if member.id in user_info[id]["usersinvited"]:
            user_info[id]["tempinvites"] -= 1
            user_info[id]["codes"][i.code] -= 1
            user_info[id]["usersinvited"][member.id].pop()
            with open("user_info.json", "w") as f:
                dump_data(user_info, f)


def dump_data(data, file):
    """Dumps a dictionary into a json file"""
    file.seek(0)
    file.truncate(0)
    json.dump(data, file, indent=4)

def create_cache(id):
    empty_inventory = {"totalinvites": 0, "tempinvites": 0, "codes": {},
                           "usersinvited": {}}
    with open("user_info.json", "r+") as f:
        stored_info = json.load(f)
        stored_info[str(id)] = empty_inventory
        dump_data(data=stored_info, file=f)

    return empty_inventory


@client.command(name="invite", aliases=["i", "invites", "invitecount", "show"])
async def invites_cmd(ctx, user: discord.Member = None):
    """Returns this week's invites and the total invites of a user."""
    if user is None:
        user = ctx.message.author
    id = str(user.id)
    with open("user_info.json", "r") as f:
        data = json.load(f)
    try:
        info = data[id]
    except KeyError:
        info = create_cache(id)
    embed = discord.Embed(title=f"**{user.display_name}'s invites:**", colour=COLOR)
    embed.set_thumbnail(url=user.avatar_url)
    embed.add_field(name=f"Current invites:", value=info["totalinvites"] - info["tempinvites"], inline=True)
    embed.add_field(name=f"All-time invites:", value=(info["totalinvites"] - info["tempinvites"]) + info["totalinvites"], inline=True)
    await ctx.send(embed=embed)


@client.command(name="leaderboard", aliases=["weekly", "wl", "weeklyleaderboard", "lb"])
async def leaderboard_cmd(ctx):
    """Shows this week's top 10 users with the most invites."""
    with open("user_info.json", "r") as f:
        data = json.load(f)
    score = {}
    for id in data:
        user = client.get_user(int(id))
        score[user.mention] = data[id]["totalinvites"] - data[id]["tempinvites"]

    sorted_score = sorted(score.items(), key=lambda x: x[1], reverse=True)

    names = ''
    scores = ''
    counter = 0
    for user in sorted_score:
        if counter <= 10:
            names += f"{user[0]}\n"
            scores += f"{user[1]}\n"
            counter += 1

    embed = discord.Embed(title="**Weekly Leaderboards**", colour=COLOR)
    embed.add_field(name="Name", value=names, inline=True)
    embed.add_field(name="Score", value=scores, inline=True)

    await ctx.send(embed=embed)


@client.command(name="alltimeleaderboard", aliases=["leaderboardtotal", "lbt", "leaderboardalltime"])
async def alltimeleaderboard_cmd(ctx):
    """Shows the top 10 users with currently the most invites all-time."""
    with open("user_info.json", "r") as f:
        data = json.load(f)
    score = {}
    for id in data:
        user = client.get_user(int(id))
        score[user.mention] = (data[id]["totalinvites"] - data[id]["tempinvites"]) + data[id]["totalinvites"]

    sorted_score = sorted(score.items(), key=lambda x: x[1], reverse=True)

    names = ''
    scores = ''
    counter = 0
    for user in sorted_score:
        if counter <= 10:
            names += f"{user[0]}\n"
            scores += f"{user[1]}\n"
            counter += 1

    embed = discord.Embed(title="**Leaderboards**", colour=COLOR)
    embed.add_field(name="Name", value=names, inline=True)
    embed.add_field(name="Score", value=scores, inline=True)

    await ctx.send(embed=embed)


client.run(token)
