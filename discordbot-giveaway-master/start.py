#This is a heavily modified and adapted version of https://github.com/AnimeHasFallen/discordbot-giveaway/
import discord
import asyncio, traceback, sys
import config
import json
import random
from discord.ext import commands
from datetime import datetime, timedelta

bot = commands.Bot(command_prefix=config.prefix, pm_help=True)
global mainguild, vip_role, mod_role

cmdsettings = {}
ongoingGiveaways = {}



##################

# Get seconds to days, hours, minutes and seconds "the number '90' will
# return '1 minute, 30 seconds'
def formatseconds(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return days, hours, minutes, seconds


# This is the function that is called every second that updates our embed
# with a new time value.
async def loopembed(title, prize, end_date, info, timeleft):
    embed = discord.Embed(color=0x0040ff, title=title)

    embed.add_field(name='Prize', value=prize, inline=False)
    embed.add_field(name='How to enter', value=info, inline=False)
    embed.add_field(name='Giveaway end date', value=end_date, inline=False)
    embed.add_field(name='Time left', value=str(timeleft), inline=False)

    return embed


async def updateEmbed(raffle, result, winners, prize, title):
    actualTitle = f'Giveaway of {title} has ended.'
    embed = discord.Embed(color=0x0040ff, title=actualTitle)
    embed.add_field(name='Prize', value=prize, inline=False)
    embed.add_field(name='Ended on', value=str(raffle['end_date']), inline=False)
    embed.add_field(name='Status', value=result, inline=False)
    mentions = []
    if winners is not None:
        if len(winners) > 1:
            for winner in winners:
                mentions.append(winner.mention)
            embed.add_field(name='Winners', value='\n'.join(mentions), inline=False)
        else:
            embed.add_field(name='Winner', value=winners[0].mention, inline=False)
    return embed


def is_allowed(ctx):
    role = config.modrole
    groups = ctx.message.author.roles  # The user's roles
    admin = False

    if ctx.guild == mainguild:
        if mod_role in groups:
            admin = True
        elif str(ctx.message.guild.owner_id) == str(ctx.message.author.id):
            admin = True

    if admin:
        return True
    else:
        ctx.send()
        return False


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        pass
    else:
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


@bot.command(pass_context=True, name="emoji",
             brief="Emoji that is supposed to be used when reacting to the giveaway")
@commands.check(is_allowed)
async def emoji(ctx, emoji: str):
    await ctx.send(f'Emoji set to {emoji}')
    if ctx.message.author.id not in cmdsettings:
        cmdsettings[ctx.message.author.id] = {}
    cmdsettings[ctx.message.author.id]['emoji'] = emoji


@bot.command(pass_context=True, name="time",
             brief="Time in seconds that the giveaway is going to run")
@commands.check(is_allowed)
async def time(ctx, time: int):
    if int(time) > 0:
        await ctx.send(f'Time set to {time}')
        if ctx.message.author.id not in cmdsettings:
            cmdsettings[ctx.message.author.id] = {}
        cmdsettings[ctx.message.author.id]['time'] = str(time)
    else:
        await ctx.send('ERROR: Has to be a positive number')


@bot.command(pass_context=True, name="winners",
             brief="The amount of winners in the giveaway.")
@commands.check(is_allowed)
async def winner_n(ctx, winner_n: int):
    if ctx.message.author.id not in cmdsettings:
        cmdsettings[ctx.message.author.id] = {}
    cmdsettings[ctx.message.author.id]['winners'] = winner_n


@bot.command(pass_context=True, name='server',
             brief="Server the giveaway will link to.")
@commands.check(is_allowed)
async def server(ctx, *arg: str):
    servername = ' '.join(arg)
    if ctx.message.author.id not in cmdsettings:
        cmdsettings[ctx.message.author.id] = {}
    for guild in bot.guilds:
        if guild.name == servername:
            cmdsettings[ctx.message.author.id]['guild'] = servername
    try:
        servername = cmdsettings[ctx.message.author.id]['guild']
        await ctx.send(f'Server set to {servername}')
    except KeyError:
        await ctx.send(f'Could not find the server {servername}. Is the bot invited, and did you spell it correctly?')


@bot.command(pass_context=True, name="prize",
             brief="Prize that the person winning is getting DM'd")
@commands.check(is_allowed)
async def prize(ctx, *args):
    arg = ' '.join(args)
    await ctx.send(f'Prize set to {arg}')
    if ctx.message.author.id not in cmdsettings:
        cmdsettings[ctx.message.author.id] = {}
    cmdsettings[ctx.message.author.id]['prize'] = arg


@bot.command(pass_context=True, name="channel",
             brief="Channel that the giveaway will be running in")
@commands.check(is_allowed)
async def channel(ctx, arg: str):
    foundChannel = discord.utils.get(mainguild.text_channels, name=arg)
    if ctx.message.author.id not in cmdsettings:
        cmdsettings[ctx.message.author.id] = {}
    cmdsettings[ctx.message.author.id]['channel'] = foundChannel.id
    await ctx.send(f'Channel set to {foundChannel.name}')


@bot.command(pass_context=True,
             brief="Do it all in one command. !doall \"emoji\" \"time\" \"number of winners\" \"prize\" \"channel\" \"server\"")
@commands.check(is_allowed)
async def doall(ctx, selected_emoji: str, selected_time: int, selected_winner_n: int, selected_title: str,
                selected_prize: str,
                selected_channel: str, selected_server):
    await emoji.callback(ctx, selected_emoji)
    await time.callback(ctx, selected_time)
    await winner_n.callback(ctx, selected_winner_n)
    await prize.callback(ctx, selected_prize)
    await channel.callback(ctx, selected_channel)
    await server.callback(ctx, selected_server)
    await start.callback(ctx)


@bot.command(pass_context=True,
             brief="Do it all in one command. !reroll", name="reroll")
@commands.check(is_allowed)
async def reroll(ctx, arg, number: int):
    with open("raffle_info.json", "r+") as f:
        stored_info = json.load(f)
        raffle = stored_info[arg]
    channel = discord.utils.get(
        mainguild.text_channels, id=raffle['channel'])
    message = await channel.fetch_message(arg)
    guild = raffle['guild']
    raffle['winners'].pop(number - 1)
    prize = raffle['prize']
    users = []
    winners = []
    for id in raffle['winners']:
        user = bot.get_user(id)
        users.append(user)
    if len(users) > 0:
        for user in users:
            winners.append(user.mention)

    newroll = bot.get_user(random.choice(raffle['userids']))
    winners.append(newroll.mention)

    actualTitle = f'Giveaway of {guild} has ended.'
    embed = discord.Embed(color=0x0040ff, title=actualTitle)
    embed.add_field(name='Prize', value=prize, inline=False)
    embed.add_field(name='Ended on', value=str(raffle['end_date']), inline=False)
    embed.add_field(name='Status', value="Ended", inline=False)

    if len(winners) > 1:
        embed.add_field(name='Winners', value='\n'.join(winners), inline=False)
    else:
        embed.add_field(name='Winner', value=winners[0], inline=False)
    await dmWinner(newroll, prize)
    await message.edit(embed=embed)


@bot.command(pass_context=True, brief="Start the giveaway")
@commands.check(is_allowed)
async def start(ctx):
    ready_to_start = True
    if ctx.message.author.id in cmdsettings:

        if 'time' not in cmdsettings[ctx.message.author.id]:
            ready_to_start = False
            await ctx.send('ERROR: Time until giveaway end not set. !help time')

        if 'guild' not in cmdsettings[ctx.message.author.id]:
            ready_to_start = False
            await ctx.send('ERROR: Server for giveaway invitation not set. !help server')

        if 'prize' not in cmdsettings[ctx.message.author.id]:
            ready_to_start = False
            await ctx.send('ERROR: Giveaway prize not set. !help prize')

        if 'winners' not in cmdsettings[ctx.message.author.id]:
            ready_to_start = False
            await ctx.send(
                'WARNING: Winner ammount wasn\'t set. Defaulted to 1 winner. !help winner\nIf 1 winner sounds good, just !start again.')
            cmdsettings[ctx.message.author.id]['winners'] = 1

        if 'channel' not in cmdsettings[ctx.message.author.id]:
            foundChannel = discord.utils.get(mainguild.text_channels, name=config.defaultchannel)
            cmdsettings[ctx.message.author.id]['channel'] = foundChannel.id

        if 'emoji' not in cmdsettings[ctx.message.author.id]:
            cmdsettings[ctx.message.author.id]['emoji'] = config.defaultemoji

    else:
        ready_to_start = False
        await ctx.send('ERROR: Nothing is configured')

    if ready_to_start:
        now = datetime.now()
        end_time = (now + timedelta(seconds=int(cmdsettings[ctx.message.author.id]['time']))).replace(microsecond=0)

        print(cmdsettings[ctx.message.author.id]['guild'])
        embed = discord.Embed(color=0x0040ff, title="Giveaway:")
        channel = discord.utils.get(
            mainguild.channels, id=cmdsettings[ctx.message.author.id]['channel'])
        theMessage = await channel.send(embed=embed)

        ongoingGiveaways[theMessage.id] = {}
        ongoingGiveaways[theMessage.id]['emoji'] = cmdsettings[ctx.message.author.id]['emoji']
        ongoingGiveaways[theMessage.id]['end_date'] = end_time
        ongoingGiveaways[theMessage.id]['channel'] = cmdsettings[ctx.message.author.id]['channel']
        ongoingGiveaways[theMessage.id]['guild'] = cmdsettings[ctx.message.author.id]['guild']
        ongoingGiveaways[theMessage.id]['winners'] = cmdsettings[ctx.message.author.id]['winners']
        ongoingGiveaways[theMessage.id]['prize'] = cmdsettings[ctx.message.author.id]['prize']

        ongoingGiveaways[theMessage.id]['task'] = bot.loop.create_task(
            reactionChecker(theMessage.id, theMessage.channel.id))
        await theMessage.add_reaction(ongoingGiveaways[theMessage.id]['emoji'])


'''
@start.error
async def start_error(ctx, error):
    await on_command_error(ctx, error)
'''


@bot.command(brief="Stops a giveaway using an ID as argument, check ID's with !g current", name="stop")
@commands.check(is_allowed)
async def stop(ctx, arg: str):
    try:
        ongoingGiveaways[arg]['task'].cancel()
        channel = discord.utils.get(
            mainguild.channels,
            id=ongoingGiveaways[arg]['channel'])
        message = await bot.get_message(channel, arg)
        newEmbed = await updateEmbed(ongoingGiveaways[arg],
                                     "Cancelled", "Nobody", server)
        await bot.edit_message(message, embed=newEmbed)
        del ongoingGiveaways[arg]
        await ctx.send(f'Stopped giveaway with ID {arg}')
    except BaseException:
        await ctx.send(f'Unable to stop giveaway with ID {arg} does it exist?')


@bot.command(brief="Shows currently running giveaways and their ID's",
             name="current")
@commands.check(is_allowed)
async def current(ctx):
    allGiveaways = ""
    for giveaway in ongoingGiveaways:
        currentGiveaway = []
        currentGiveaway.append("ID: " + str(giveaway))
        for item in ongoingGiveaways[giveaway]:
            if item == "emoji":
                currentGiveaway.append(
                    str(item) + ": " + str(ongoingGiveaways[giveaway][item]))
            elif item == "message":
                currentGiveaway.append(
                    str(item) + ": " + str(ongoingGiveaways[giveaway][item]))
            elif item == "end_date":
                currentGiveaway.append(
                    str(item) + ": " + str(ongoingGiveaways[giveaway][item]))

        allGiveaways = allGiveaways + str(currentGiveaway[0]) + " " + str(currentGiveaway[1]) + "\n" + str(
            currentGiveaway[2]) + "\n" + str(currentGiveaway[3]) + "\n" + str(currentGiveaway[4]) + "\n" + str(
            currentGiveaway[5]) + "\n" + str(currentGiveaway[6]) + "\n" + str(currentGiveaway[7]) + "\n\n"
    # allGiveaways.append(currentGiveaway)

    await ctx.send(f'Current giveaways:\n {allGiveaways}')


@bot.command(pass_context=True,
             brief="Shows your current settings",
             name="settings")
@commands.check(is_allowed)
async def settings(ctx):
    allsettings = ""
    if ctx.message.author.id in cmdsettings:
        for item in cmdsettings[ctx.message.author.id]:
            allsettings = allsettings + \
                          str(item) + ": " + str(cmdsettings[ctx.message.author.id][item]) + "\n"
        # allsettings.append([item,cmdsettings[ctx.message.author.id][item]])

        await ctx.send(f'Current settings:\n {allsettings}')
    else:
        await ctx.send('ERROR: Nothing is configured')


def dump_data(data, file):
    """Dumps a dictionary into a json file"""
    file.seek(0)
    file.truncate(0)
    json.dump(data, file, indent=4)

###############
async def reactionChecker(messageID, channelID):
    allWhoReacted = []
    guild = mainguild
    channel = discord.utils.get(guild.text_channels, id=channelID)
    message = await channel.fetch_message(messageID)
    prize = ongoingGiveaways[messageID]['prize']
    end_date = ongoingGiveaways[messageID]['end_date']
    emoji = ongoingGiveaways[messageID]['emoji']
    server = ongoingGiveaways[messageID]['guild']
    winner_ammount = int(ongoingGiveaways[messageID]['winners'])

    server2_users = []
    for x in bot.guilds:
        if x.name == server:
            inviteobj = await x.text_channels[0].create_invite()
            invite = inviteobj.url
            print(x.members)
            server2_users = x.members

    title = f"Giveaway: {server}."
    info = f"React with {emoji} and join {invite} to enter."
    # Grab the time the raffle will end and format it
    leaving_date = datetime.strptime(str(end_date), '%Y-%m-%d %H:%M:%S')

    now = datetime.now()  # Grab the current time
    # Do the final raffle time minus current time to get remaining time
    time_delta = (leaving_date - now)
    # Turns the probably-broken-time into seconds
    time_dif = time_delta.days * 24 * 3600 + time_delta.seconds
    while time_dif >= 0:
        await asyncio.sleep(1)

        now = datetime.now()  # Grab the current time

        # Do the final raffle time minus current time to get remaining time
        time_delta = (leaving_date - now)

        # Turns the probably-broken-time into seconds
        time_dif = time_delta.days * 24 * 3600 + time_delta.seconds

        time_left = "%d days, %d hours, %d minutes, %d seconds" % formatseconds(
            time_dif)
        new_embed = await loopembed(title, prize, end_date, info, time_left)
        await message.edit(embed=new_embed)

    message = await channel.fetch_message(messageID)
    all_reactions = message.reactions
    for reaction in all_reactions:
        if str(reaction.emoji) == emoji:
            this_kind_of_reactions = await reaction.users().flatten()
            for oneReaction in this_kind_of_reactions:
                if oneReaction in guild.members:
                    if not oneReaction == bot.user:
                        allWhoReacted.append(oneReaction)

    final = []
    for user in allWhoReacted:  # For every user that reacted to the original message (users1)
        if vip_role in user.roles:  # If the user has VIP
            counter = int(config.VIP_N)
            while counter:  # Adds them to the list (counter) times.
                final.append(user)
                counter -= 1
        elif user in server2_users:  # If they don't have VIP and they joined the second server
            final.append(user)  # Adds them to the list.
    winners = []
    print(ongoingGiveaways[messageID])
    if len(final) > 0:
        i = winner_ammount
        while i:
            winner = random.choice(final)
            while winner in final:
                final.remove(winner)
            winners.append(winner)
            i -= 1
            result = await dmWinner(winner, prize)
    else:
        result = ["NO_WINNER", ""]
    if result[0] == "OK":
        new_embed = await updateEmbed(ongoingGiveaways[messageID], "Ended", winners, prize, server)
        userids = []
        winnerids = []
        for user in final:
            userids.append(user.id)
        for user in winners:
            winnerids.append(user.id)
            ongoingGiveaways[messageID]['winnerusers'] = winnerids
        ongoingGiveaways[messageID]['userids'] = userids

        create_cache(messageID)
        await message.edit(embed=new_embed)
    elif result[0] == "NO_WINNER":
        new_embed = await updateEmbed(ongoingGiveaways[messageID], "Ended without a winner", None, prize, server)
        await message.edit(embed=new_embed)
    elif result[0] == "DM_ERROR":
        new_embed = await updateEmbed(ongoingGiveaways[messageID], "Ended with error", None, prize, server)
        await message.edit(embed=new_embed)
    del ongoingGiveaways[messageID]

def create_cache(id):
    print(ongoingGiveaways[id]['end_date'])
    saved = {'end_date': str(ongoingGiveaways[id]['end_date']), 'channel': ongoingGiveaways[id]['channel'],\
             'guild': ongoingGiveaways[id]['guild'], 'winners': ongoingGiveaways[id]['winnerusers'],\
             'prize': ongoingGiveaways[id]['prize'], 'userids': ongoingGiveaways[id]['userids']}
    with open("raffle_info.json", "r+") as f:
        stored_info = json.load(f)
        stored_info[id] = saved
        dump_data(data=stored_info, file=f)

async def dmWinner(winner, prize):
    print("Winner is", str(winner))

    try:
        await winner.send(f"You have won {str(prize)}")
        return ["OK", winner]
    except BaseException:
        print("Error sending DM to ", str(winner),
              " make sure user allows DM's and exists on the guild")
        return ["DM_ERROR", ""]


##################

@bot.event
async def on_ready():
    global mainguild, vip_role, mod_role
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    for x in bot.guilds:
        print(1)
        if x.name == config.mainserver:
            mainguild = x
    vip_role = discord.utils.get(mainguild.roles, name=config.vip)
    mod_role = discord.utils.get(mainguild.roles, name=config.modrole)


bot.run(config.token)
