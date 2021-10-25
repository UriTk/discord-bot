import discord, sys, random, json
from discord.ext import commands, menus, tasks
from datetime import datetime

# Hi dev! I'm the second and latest programmer on this bot.
# A few things that might help you out:
#
# -Documentation is mostly mine, but there's some traces of my predecessor dev around there.
# You should be able to differentiate us with capitalization.
# Non-capitalized comments are most likely the predecessor dev. Or a really tired me, but probably the old dev.
#
# -The original dev used "An experimental extension menu that makes working with reaction menus a bit easier."
# It's not bad, actually. Grab it here. https://github.com/Rapptz/discord-ext-menus
#
# -Predecessor dev referred to Gachas as "cards" a lot for some reason, so you might see that a bunch.
#
# -I generally don't do this, but this is a big messy piece of code, so if you need to ask something about it, Uri#7275.
# Take it as a favour from a stranger? Feel free to tell me how bad my code is, too.
#
# -If you end up updating the server's files, remember to avoid overwriting stuff like user_info.
# You'll delete a bunch of progress if you do that.


sys.path.append("..")  # allows UtilityFiles to import
from UtilityFiles.constants import COLOR, RARITY_MAP, DAILY_TIME, PREFIX, GRADES, \
    RARITY_VALUE  # imports settings

# imports utility functions, will be split up later
from UtilityFiles.util import get_inventory, exel_reader, get_gachas, add_card, get_pool, dump_data, \
    is_allowed, NoGachas, ShopConfirmMenu, TradeConfirmMenu, achievement_checker, \
    GachaCard, CardMenu, CardMenuSource, ShowGachaMenu, ConvertGachaMenu, get_score, LotteryGachaMenu

# Define global constants
GACHA_DATA = exel_reader("UtilityFiles/GACHAUNITS.xlsx")


# <editor-fold desc="TODO: list">
# You can delete this if you want, dev. I just use this to keep track of my things.
# -=-=- MAIN THINGS TO DO -=-=-

# -=-=- CURRENTLY DOING -=-=-
# TODO: Achievements
# Make achievement_checker(in util.py) actually save achievement changes to achievements.json
# (should be easy, a modified version of how gachas are saved or something similar would work.)
#
# Make it announce when someone gets an achievement. A "Congratulations!" kind of deal.
#
# Make it not hell. (Actually possible?) Improve readability as much as possible, balance that with optimization.
#
# Probably make a class for achievements once we start actually working with them properly.
# Everything is laid out neatly for a class, after all.

# -=-=- NEEDS BUG FIX/MODIFICATION -=-=-
# TODO: Weekly bonus and daily lottery.
# Make sure they don't fuck up when the bot disconnects -
# give their respective task loops a failsafe to fall on in said case. (best way to do this?)
#
#
# TODO: Store management overall:
# Tickets don't need to show statistics. (What did you mean by this, 7-AM-Caffeinated-Me?)
# Add confirmation on shop purchase.
# Make the store look nicer if possible. It's a bit bland right now?
# </editor-fold>

class GachaGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test", aliases=["t"])
    async def test_cmd(self, ctx):
        gachas = get_gachas(ctx.author, GACHA_DATA)
        print(str(gachas))

    # <editor-fold desc="Inventory">
    # Main inventory command.
    # This shows all the saved stats of said user (from user_info.json).
    @commands.command(name="inventory", aliases=["i"])
    async def inventory_cmd(self, ctx, *, user: discord.Member = None):
        """Shows the inventory of the user"""
        user = ctx.author if user is None else user  # if no user is inputted then it does the command author
        inventory = get_inventory(user.id)  # retrieves the inventory of a certain user

        # gets the amount of each rarity a player has
        rarity_amounts = {}
        for gacha_id in inventory["gachas"].keys():
            rarity = RARITY_MAP[
                GACHA_DATA[str(gacha_id)]["Grade"]]  # gets the rarity and maps it to a more common name
            if rarity in rarity_amounts.keys():
                rarity_amounts[rarity] += inventory["gachas"][gacha_id]  # adds the amount of gachas a user has
            else:
                rarity_amounts[rarity] = inventory["gachas"][gacha_id]  # adds the amount of gachas a user has

        # creates and sends embed with inventory info
        inventory_embed = discord.Embed(title=f"**{user.name}'s Inventory:**", colour=COLOR)
        inventory_embed.add_field(name="**Coins:**", value=inventory["coins"], inline=False)
        inventory_embed.add_field(name="**Tickets:**", value=inventory["tickets"], inline=False)
        inventory_embed.add_field(name="**Special Tickets:**", value=inventory["special_tickets"], inline=False)
        inventory_embed.add_field(name="**Super Tickets:**", value=inventory["super_tickets"], inline=False)
        inventory_embed.add_field(name="**Ultra Tickets:**", value=inventory["ultra_tickets"], inline=False)
        for rarity, amount in rarity_amounts.items():
            inventory_embed.add_field(name=f"**{rarity} Gachas:**", value=amount, inline=False)
        await ctx.send(embed=inventory_embed)

    # sends embed when inventory command could not find a user
    @inventory_cmd.error
    async def info_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=discord.Embed(title='That user could not be found', colour=COLOR))
        else:
            print(f"Error in Inventory Command:\n{error}")

    # </editor-fold>

    # <editor-fold desc="Store">
    #  The command that will add items to the store manually.
    @commands.command(pass_context=True, name='storeAdd')
    @commands.check(is_allowed)
    async def store_add_cmd(self, ctx, itemraw, price=None):
        if price is None:  # Make sure the user inputs a price in, and that the price is a number.
            await ctx.send("Please input a price.")
            return
        try:
            price = int(price)
        except ValueError:
            await ctx.send(f"Invalid price. Use the command like {PREFIX}storeadd [item] [price].")
            return

        cards = get_pool("all")  # Grabs all the cards from the excel sheet.
        try:
            card_id = int(itemraw)  # checks if the data was a card id
            try:
                card = [card for card in cards if
                        card_id == card.card_id][0]  # retrieves a card with the correct id
                item = card.card_id
            except IndexError:
                await ctx.send("Could not find unit.")
                return
        except ValueError:  # If the data was text (i.e. a card's name or a ticket)
            if itemraw == "normal":  # Checks if it's a regular roll, or if not, which rarity it is
                item = "Ticket"  # Would using a class or something for this work? switch statements don't exist in python so
            elif itemraw == 'special':
                item = "Special Ticket"
            elif itemraw == 'super':
                item = "Super Ticket"
            elif itemraw == 'ultra':
                item = "Ultra Ticket"
            else:
                try:
                    card = [card for card in cards if
                            itemraw.lower() == card.name.lower()][
                        0]  # Retrieves a card with the correct id (mostly makes sure the card exists)
                    item = card.card_id
                except IndexError:  # If no gacha or ticket was found
                    await ctx.send(
                        f"Could not find unit/ticket. For tickets, please use {PREFIX}storeadd [normal/special/super/ultra] [price]")
                    return
        with open("UtilityFiles/shop.json",
                  "r+") as f:  # If everything went right, save into the shop json, into the "temporal" section.
            stored_info = json.load(f)
            stored_info['temp'][item] = price
            dump_data(data=stored_info, file=f)
        await ctx.send("Successfully added item.")

    # Removes a specific item from the store, not including the permanent items.
    @commands.command(pass_context=True, name='storeremove', alias=["removestore", "storedelete", "deletestore"])
    @commands.check(is_allowed)
    async def store_remove_cmd(self, ctx, value):
        try:  # Make sure the value inputted was a number.
            value = int(value) - 1  # The user will expect the "list" to start from 1, not 0, so do -1.
        except ValueError:
            await ctx.send("Invalid argument. Argument should be a number.")

        with open("UtilityFiles/shop.json", "r+") as f:
            stored_info = json.load(f)
            try:
                string = list(stored_info['temp'])[value]
            except IndexError:
                await ctx.send("Could not find that item. Are you trying to remove a permanent item?")
                return
            stored_info['temp'].pop(string)
            dump_data(data=stored_info, file=f)
        await ctx.send("Successfully removed item.")

    #  The command to view the store
    #  The store separates in two sections, temporal and permanent items. Check shop.json and you should get it.
    @commands.command(name='store')
    async def store_cmd(self, ctx):
        with open("UtilityFiles/shop.json", "r+") as f:
            stored_info = json.load(f)  # Grab the shop info

        counter = 0
        items = []
        pool = get_pool('all')
        embed = discord.Embed(title="Store", colour=COLOR)
        for stored_item in stored_info['temp']:  # Starts listing out the temp shop items into embed
            counter += 1
            try:  # Try to see if the item is a gacha. If it is, list it that way.
                item_id = int(stored_item)
                item = [card for card in pool if
                        item_id == card.card_id][0]  # retrieves a card with the correct id
                embed.add_field(name=f"{counter}:",
                                value=f"#{item.card_id} | {item.name} | {RARITY_MAP[item.rarity]} | {item.show}\n*{stored_info['temp'][stored_item]} coins.*",
                                inline=False)
            except ValueError:  # If it's something other than a gacha, i.e. a ticket, just put it up plain like that on the embed.
                embed.add_field(name=f"{counter}:", value=f"{stored_item}\n*{stored_info['temp'][stored_item]} coins.*",
                                inline=False)
        for stored_item in stored_info[
            'perm']:  # In the end of the list, put in the permanent items. (No gachas here, for now)
            counter += 1
            embed.add_field(name=f"{counter}:", value=f"{stored_item}\n*{stored_info['perm'][stored_item]} coins.*",
                            inline=False)
        await ctx.send(embed=embed)

    #  The command you use to buy something from the store. Bit gross. TODO: Make this not be shit. (Make it "!shit"?)
    #  (I never fixed this, sorry dev!)
    @commands.command(name='buy')
    async def buy_cmd(self, ctx, itemraw=None):
        if itemraw is None:  # If no item was inputted
            ctx.send(
                f"Please input a number if you wanna buy something. For example, to buy the second item on list, input {PREFIX}buy 2")
            return

        try:  # Make sure the item was a number
            itemraw = int(itemraw)
            itemraw -= 1
        except ValueError:
            await ctx.send(
                f"Invalid choice. Please input a number if you wanna buy something. To buy the second item on list, input {PREFIX}buy 2")
            return

        with open("UtilityFiles/shop.json", "r+") as f:
            stored_info = json.load(f)

        try:  # Try to buy an item from the temporal list.
            item = list(stored_info['temp'])[itemraw]
            temporal = True
        except IndexError:  # If it's not on the temporal list, it's probably on the end of the actual shop list, along the "permanent" items.
            itemraw -= len(list(stored_info['temp']))
            try:
                item = list(stored_info['perm'])[itemraw]
                temporal = False
            except IndexError:  # If it's not here either, the item doesn't exist.
                await ctx.send("Could not find that item.")
                return

        inventory = get_inventory(str(ctx.author.id))
        pool = get_pool('all')
        #  The gross part, these two do almost the same thing, but they check differently depending on if the item is in the temp or perm list.
        if temporal:
            if stored_info['temp'][item] <= inventory["coins"]:  # If the user has enough coins
                inventory["coins"] -= stored_info['temp'][item]  # Reduce the coins by the respective amount
                try:
                    item_id = int(item)  # Check if the item is a gacha or not
                    is_gacha = True
                except ValueError:
                    is_gacha = False
            else:  # If the user does not have enough coins
                await ctx.send("Not enough coins!")
                return
        else:
            if stored_info['perm'][item] <= inventory["coins"]:  # If the user has enough coins
                inventory["coins"] -= stored_info['perm'][item]  # Reduce the coins by the respective amount
                try:
                    item_id = int(item)  # Check if the item is a gacha or not
                    is_gacha = True
                except ValueError:
                    is_gacha = False
            else:  # If the user does not have enough coins
                await ctx.send("Not enough coins!")
                return

        if is_gacha:  # If it's a gacha, get the card.
            item = [card for card in pool if
                    item_id == card.card_id][0]  # retrieves a card with the correct id

        #  Start the purchase confirmation.
        await ShopConfirmMenu(ctx, item, is_gacha).start(ctx)

    # Cleans store.json's temp items
    @commands.command(pass_context=True, name='clearstore', aliases=["storeclear"])
    @commands.check(is_allowed)
    async def clear_store_cmd(self, ctx):
        with open("UtilityFiles/shop.json", "r+") as f:
            stored_info = json.load(f)
            stored_info['temp'].clear()
            dump_data(data=stored_info, file=f)

    # Randomizes the store. It grabs 1 random common (costs 3 coins), 1 rare (7), 1 super rare (12) and 1 ultra rare(25)
    # Then it randomizes 1 Super and 1 Ultra Rare units to be on "Sale" for 10 and 20 tickets respectively.
    @commands.command(pass_context=True, name='randomizestore',
                      aliases=["storerandomize", "randomstore", "storerandom"])
    @commands.check(is_allowed)
    async def randomize_store_cmd(self, ctx):
        #  Grabs all four currently-set pools, and picks from them at random.
        commonpool = get_pool("common")
        rarepool = get_pool("rare")
        superpool = get_pool("super_tickets")
        ultrapool = get_pool("ultra_tickets")

        common = random.choice(commonpool)
        rare = random.choice(rarepool)
        super = random.choice(superpool)
        superpool.remove(super)  # Make sure the "sale" items don't end up as duplicates.
        ultra = random.choice(ultrapool)
        ultrapool.remove(ultra)
        supersale = random.choice(superpool)
        ultrasale = random.choice(ultrapool)

        with open("UtilityFiles/shop.json", "r+") as f:  # Update shop.json
            stored_info = json.load(f)
            stored_info['temp'][common.card_id] = 3
            stored_info['temp'][rare.card_id] = 7
            stored_info['temp'][super.card_id] = 12
            stored_info['temp'][ultra.card_id] = 25
            stored_info['temp'][supersale.card_id] = 10
            stored_info['temp'][ultrasale.card_id] = 20
            dump_data(data=stored_info, file=f)
        await ctx.send("Randomized the store.")

    # </editor-fold>

    # <editor-fold desc="Set Pool">
    # Sets the pool for drawable Gacha in normal/super/ultra rolls.
    @commands.command(pass_context=True, name='setPool')
    @commands.check(is_allowed)
    async def set_pool_cmd(self, ctx, *ids):
        gachas = exel_reader("UtilityFiles/GACHAUNITS.xlsx")  # Reads our Gacha list.
        grades = {}
        pool = get_pool("all")  # Gets a list of all the gachas in GACHAUNITS.
        allgacha = False
        for setting in GRADES:  # We grab the settings for how often a rarity should be put on the pool.
            grades[setting.split(":")[0]] = int(setting.split(":")[1])
        if ids == ('all',):  # If instead of a bunch of IDs, the user inputs "all", just puts all the Gachas in.
            ids = range(1, len(gachas) + 1)
            allgacha = True

        gachapool = []
        commonpool = []
        rarepool = []
        superpool = []
        ultrapool = []

        for id_raw in ids:  # For every gacha inputted in command (or all of them with 'all')
            id = int(id_raw)
            card = [card for card in pool if id == card.card_id][0]  # Grabs the actual Gacha based on ID
            if allgacha:
                if card.header == "Achievements":  # Ignore achievement-specific cards.
                    continue
            rarity = grades[card.rarity]  # Reads it's rarity.
            counter = rarity  # Checks how many times it should be added to the normal pool

            if card.rarity == 'C':
                commonpool.append(id)
            elif card.rarity == 'R':
                rarepool.append(id)
            elif card.rarity == 'SR':  # Adds them to the super/ultra pool if need be
                superpool.append(id)
            elif card.rarity == 'UR':
                ultrapool.append(id)

            while counter > 0:  # Adds them X times to the pool, depending on rarity.
                counter -= 1
                gachapool.append(id)
        # Writes the stuff we set up to it's respective pool
        with open("UtilityFiles/gacha_pool.json", "r+") as f:
            dump_data(data=gachapool, file=f)
        with open("UtilityFiles/gacha_pool_common.json", "r+") as f:
            dump_data(data=commonpool, file=f)
        with open("UtilityFiles/gacha_pool_rare.json", "r+") as f:
            dump_data(data=rarepool, file=f)
        with open("UtilityFiles/gacha_pool_super.json", "r+") as f:
            dump_data(data=superpool, file=f)
        with open("UtilityFiles/gacha_pool_ultra.json", "r+") as f:
            dump_data(data=ultrapool, file=f)
        await ctx.send("Updated the gacha pool!")

    # Sets the gacha for the "Special Pool", only drawable on special rolls. As you may imagine.
    # Basically a copypaste of above, with less stuff. Refer to above setpool if you need proper documentation.
    @commands.command(pass_context=True, name='setspecialpool', alias='setpoolspecial')
    @commands.check(is_allowed)
    async def setspecialpool_cmd(self, ctx, *ids):
        gachas = exel_reader("UtilityFiles/GACHAUNITS.xlsx")
        grades = {}
        pool = get_pool("all")
        for setting in GRADES:
            grades[setting.split(":")[0]] = int(setting.split(":")[1])
        if ids == ('all',):
            ids = range(1, len(gachas) + 1)
        gacha_pool = []
        for id_raw in ids:
            id = int(id_raw)
            card = [card for card in pool if id == card.card_id][0]
            rarity = grades[card.rarity]
            counter = rarity
            while counter > 0:
                counter -= 1
                gacha_pool.append(id)
        with open("UtilityFiles/gacha_pool_special.json", "r+") as f:
            dump_data(data=gacha_pool, file=f)
        await ctx.send("Updated the special gacha pool!")

    # </editor-fold>

    # <editor-fold desc="AddX/AddAllX">
    #  This section is fairly self explanatory. They are commands to add to user's inventories.
    #  Be it adding coins, tickets, or specific Gacha units to one or every user.
    #  Aimed for Admin users.
    @commands.command(pass_context=True, name="addticket", aliases=["addtickets", "giveticket", "givetickets"])
    @commands.check(is_allowed)
    async def addticket_cmd(self, ctx, user: discord.Member = None, rarity="normal", amount=1):
        if user is None:
            await ctx.send("Please put in the user you want to give the ticket(s) to.")

        if rarity == "normal":  # Checks if it's a regular roll, or if not, which rarity it is
            ticket = "tickets"  # Would using a class or something for this work and be better? switch statements don't exist in python so
        elif rarity == 'special':
            ticket = "special_tickets"
        elif rarity == 'super':
            ticket = "super_tickets"
        elif rarity == 'ultra':
            ticket = "ultra_tickets"
        else:
            await ctx.message.channel.send(
                f"Rarity not recognized. Please use one of these: \"{PREFIX}addticket (user) (normal/special/super/ultra) (amount)\"")
            return

        with open("UtilityFiles/user_info.json", "r+") as f:  # Saves the data we changed
            stored_info = json.load(f)
            stored_info[str(user.id)][ticket] += int(amount)
            dump_data(data=stored_info, file=f)
        await ctx.send(f"Gave {user.mention} {amount} {rarity} ticket(s)!")

    @commands.command(pass_context=True, name="addcoin", aliases=["addcoins", "givecoin", "givecoins"])
    @commands.check(is_allowed)
    async def addcoin_cmd(self, ctx, user: discord.Member = None, amount=1):
        if user is None:
            await ctx.send("Please input in a user to give coins to.")

        with open("UtilityFiles/user_info.json", "r+") as f:  # Saves the data we changed
            stored_info = json.load(f)
            stored_info[str(user.id)]["coins"] += int(amount)
            dump_data(data=stored_info, file=f)
        await ctx.send(f"Gave {user.mention} {amount} coin(s)!")

    @commands.command(pass_context=True, name="addallticket",
                      aliases=["givealltickets", "giveallticket", "addalltickets"])
    @commands.check(is_allowed)
    async def addallticket_cmd(self, ctx, rarity="normal", amount=1):
        if rarity == "normal":  # Checks if it's a regular roll, or if not, which rarity it is
            ticket = "tickets"  # Would using a class or something for this work? switch statements don't exist in python so
        elif rarity == 'special':
            ticket = "special_tickets"
        elif rarity == 'super':
            ticket = "super_tickets"
        elif rarity == 'ultra':
            ticket = "ultra_tickets"
        else:
            await ctx.message.channel.send(
                f"Rarity not recognized. Please use one of these: \"{PREFIX}addallticket normal/special/super/ultra amount\"")
            return

        with open("UtilityFiles/user_info.json", "r+") as f:  # saves the data we changed
            stored_info = json.load(f)
            for member in stored_info:
                stored_info[member][ticket] += int(amount)
                dump_data(data=stored_info, file=f)
        await ctx.send(f"Gave everyone {amount} {rarity} ticket(s)!")

    @commands.command(pass_context=True, name="addallcoin", aliases=["aac", "giveallcoin", "giveallcoins"])
    @commands.check(is_allowed)
    async def addallcoin_cmd(self, ctx, amount=1):
        with open("UtilityFiles/user_info.json", "r+") as f:  # saves the data we changed
            stored_info = json.load(f)
            for member in stored_info:
                stored_info[member]['coins'] += int(amount)
                dump_data(data=stored_info, file=f)
        await ctx.send(f"Gave everyone {amount} coin(s)!")

    # </editor-fold>

    # <editor-fold desc="Give">
    @commands.command(pass_context=True, name="give")
    @commands.check(is_allowed)
    async def give_cmd(self, ctx, user: discord.Member = None, *, gacha_info=None):
        if user is None:  # Checks if the user and gacha was inputted
            await ctx.send("Please specify a user to give a gacha to.")
            return
        elif gacha_info is None:
            await ctx.send("Please specify a gacha.")
            return

        pool = get_pool("all")  # Gets a pool of all the gachas to search through
        inventory = get_inventory(str(user.id))  # gets the user's inventory

        # Admin command, so we don't need to check if a name was used instead of an ID.
        try:
            card_id = int(gacha_info)
            card = [card for card in pool if card_id == card.card_id][0]  # retrieves a card with the correct id
        except IndexError:  # if card[0] doesnt exist
            await ctx.send("Couldn't find the Gacha.")
            return

        gachas = inventory["gachas"]  # retrieves the user's gachas
        add_card(user, str(card.card_id))  # adds a new card to the gachas

        # finds out how many of the card the user now has
        if str(card.card_id) in gachas.keys():  # if the user has the card already
            card.amount = gachas[
                              str(card.card_id)] + 1  # card.amount is set to how many of the card the user now has
            message = f"Congratulations, you just got another {card.name}! You now have {card.amount} {card.name}'s"
        else:  # the card must be new
            card.amount = 1  # the amount is by default 1
            message = f"Congratulations, you just got a new card, {card.name}!"

        if card:  # if there is a card with the correct id
            await ctx.send(embed=discord.Embed(title=message, colour=COLOR))
            await ShowGachaMenu(card).start(ctx)  # creates a menu to show the card
            achievement_checker(ctx.author, "unitadd", card)  # Checks achievements

    # </editor-fold>

    # <editor-fold desc="Daily">
    #  This is the !daily command. It's a bit of a mess, and could possibly be a lot better.
    @commands.command(name="daily", aliases=["d"])
    async def daily_cmd(self, ctx):
        dt = datetime.now()  # Grabs the time and date
        ymd = int(dt.strftime("%Y%m%d"))  # Formats the date properly into an int
        h = int(dt.strftime("%H"))  # Same thing, but with what hour it is
        inventory = get_inventory(str(ctx.author.id))  # gets the user's inventory
        last_login = inventory["last_login"]
        consecutive = inventory["consecutive_logins"]

        if ymd > last_login:  # If the last login wasn't today
            if h > DAILY_TIME:  # Checks if the command is being used after the daily reset time
                if ymd - last_login == 1:  # If the last login wasn't more than a day ago
                    consecutive += 1  # Marks that the user has been on one more day in a row
                else:
                    consecutive = 1  # If the last login was more than a day ago, resets the login counter

                if (consecutive % 7) == 0:  # If "consecutive logins" is a multiplier of 7, award bonus tickets
                    await ctx.send(
                        "You have been given 3 tickets as a daily award.\nYou've also been given 3 bonus tickets and 5 coins for your 7th consecutive login!")
                    inventory["tickets"] += 6
                    inventory["coins"] += 3
                elif consecutive > 0:
                    await ctx.send(
                        f"You have been given 3 tickets as a daily award.\nYou've logged in {consecutive} consecutive days.")
                    inventory["tickets"] += 3
                else:
                    await ctx.send("You have been given 3 tickets as a daily award.")
                    inventory["tickets"] += 3

                with open("UtilityFiles/user_info.json", "r+") as f:  # Saves the data we changed
                    stored_info = json.load(f)
                    stored_info[str(ctx.author.id)]["tickets"] = inventory["tickets"]
                    stored_info[str(ctx.author.id)]["last_login"] = ymd
                    stored_info[str(ctx.author.id)]["consecutive_logins"] = consecutive
                    stored_info[str(ctx.author.id)]["coins"] = inventory["coins"]
                    dump_data(data=stored_info, file=f)
            elif DAILY_TIME - h == 1:  # For grammar purposes, if it's been a day but there's hours to go. Might as well
                await ctx.send(
                    f"You'll be able to do your daily in an hour.")  # Checks and tells the user it's an hour till reset
            else:
                await ctx.send(
                    f"You'll be able to do your daily in {DAILY_TIME - h} hours")  # Or tells him how many hours are left
        else:  # If the user has already done !daily today, tell them.
            await ctx.send("You have already done your daily today!")

    # </editor-fold>

    # <editor-fold desc="Loops">
    #  These loops will execute weekly and daily, respectively.

    #  The Weekly loop will check the current score leaders. It will grab the first, second and last place (not third)
    #  and give them respective prizes.
    @tasks.loop(hours=168)
    async def weekly_rewards(self, ctx):
        user_score = {}
        with open("UtilityFiles/user_info.json", "r") as f:
            stored_info = json.load(f)
        for userid in stored_info:
            user = self.bot.get_user(int(userid))
            if user is not None:
                score = get_score(user, GACHA_DATA)
                user_score[userid] = score
        sorted_obj = sorted(user_score.items(), key=lambda x: x[1],
                            reverse=True)  # Sorts the user list depending on score
        embed = discord.Embed(title=f"**Weekly Bonus!**", colour=COLOR)
        #  sorted_obj[0][0] = Name (Well, discord ID for mentions.)
        #  sorted_obj[0][1] = Score
        embed.add_field(name="First place:",
                        value=f"<@{sorted_obj[0][0]}> with {sorted_obj[0][1]} points!\nReward: 5 tickets and 10 coins! ",
                        inline=False)
        embed.add_field(name="Second place:",
                        value=f"<@{sorted_obj[1][0]}> with {sorted_obj[1][1]} points!\nReward: 2 tickets and 5 coins! ",
                        inline=False)
        embed.add_field(name="Last place:",
                        value=f"<@{sorted_obj[-1][0]}> with {sorted_obj[-1][1]} points!\nReward: 3 tickets and 5 coins! ",
                        inline=False)
        await ctx.send(embed=embed)

        with open("UtilityFiles/user_info.json", "r+") as f:  # saves the data we changed
            stored_info = json.load(f)
            stored_info[str(sorted_obj[0][0])]["tickets"] += 5
            stored_info[str(sorted_obj[1][0])]["tickets"] += 2
            stored_info[str(sorted_obj[-1][0])]["tickets"] += 3
            stored_info[str(sorted_obj[0][0])]["coins"] += 10
            stored_info[str(sorted_obj[1][0])]["coins"] += 5
            stored_info[str(sorted_obj[-1][0])]["coins"] += 5
            dump_data(data=stored_info, file=f)

    @tasks.loop(hours=24)
    #  This is a Daily Lottery.  You'd think it gives a random user coins or something, but it actually grabs a random
    #  gacha unit, checks who owns that gacha (the winners), and gives them tickets.
    async def daily_lottery(self, ctx):
        winners = []
        with open("UtilityFiles/user_info.json", "r+") as f:
            stored_info = json.load(f)
        pool = get_pool('all')
        card = random.choice(pool)  # picks a random card from the pool
        for userid in stored_info:
            if str(card.card_id) in stored_info[userid]["gachas"].keys():
                winners.append(userid)
        if not winners:
            message = "Nobody owns this unit."
        else:
            message = '>\n<@'.join(winners)
            message = ''.join(('<@', message, '>'))
        with open("UtilityFiles/user_info.json", "r+") as f:
            stored_info = json.load(f)
            for winner in winners:
                stored_info[str(winner)]["tickets"] += 3
            dump_data(data=stored_info, file=f)

        embed = discord.Embed(title=f"**Lucky Lottery of the day!**", colour=COLOR)
        embed.add_field(name="**Prize & Unit:**",
                        value=f"Anyone who owns {card.name} from {card.show} will be given 3 tickets as a reward!",
                        inline=False)
        embed.add_field(name="**Winners:**", value=message, inline=False)
        await ctx.send(embed=embed)
        await LotteryGachaMenu(card).start(ctx)  # creates a menu to show the card

    #  Starts the respective loops with commands.
    @commands.command(pass_context=True, name="startdailyloop")
    @commands.check(is_allowed)
    async def startdailyloop_cmd(self, ctx):
        self.daily_lottery.start(ctx)

    @commands.command(pass_context=True, name="startweeklyloop")
    @commands.check(is_allowed)
    async def startweeklylooploop_cmd(self, ctx):
        self.weekly_rewards.start(ctx)

    # </editor-fold>

    # <editor-fold desc="Leaderboard">
    # Self explanatory, grabs the user scores and lays them down in a sorted leaderboard manner.
    @commands.command(name="leaderboard", aliases=["lb"])
    async def leaderboard_cmd(self, ctx):
        user_score = {}
        with open("UtilityFiles/user_info.json", "r") as f:
            stored_info = json.load(f)
        for userid in stored_info:
            user = self.bot.get_user(int(userid))
            if user is not None:
                score = get_score(user, GACHA_DATA)
                user_score[user.mention] = score
        sorted_obj = sorted(user_score.items(), key=lambda x: x[1], reverse=True)
        names = ''
        scores = ''
        for user in sorted_obj:
            names += f"{user[0]}\n"
            scores += f"{user[1]}\n"

        embed = discord.Embed(title=f"**Leaderboards**", colour=COLOR)
        embed.add_field(name="Name", value=names, inline=True)
        embed.add_field(name="Score", value=scores, inline=True)

        await ctx.send(embed=embed)

    # </editor-fold>

    # <editor-fold desc="Collection">
    # This part was mostly (completely?) coded by my predecesor dev. Best way to see what it does is using it.
    @commands.command(name="collection", aliases=["col"])
    async def collection_cmd(self, ctx, *, user: discord.Member = None):
        """Shows a user's gacha collection"""
        user = ctx.author if user is None else user  # if no user is inputted then it does the command author
        cards = get_gachas(user, excel_data=GACHA_DATA)  # retrieves the user's cards
        pages = CardMenu(source=CardMenuSource(cards),
                         clear_reactions_after=True)  # creates an embed menu using discord.Menus
        await pages.start(ctx)  # starts the menu

    @collection_cmd.error
    async def collection_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=discord.Embed(title='That user could not be found', colour=COLOR))
        if isinstance(error, commands.errors.CommandInvokeError):  # if the user has no gachas
            await ctx.send(embed=discord.Embed(title='That user has no gachas in their collection', colour=COLOR))
        else:
            print(f"Error in Collection Command:\n{error}")

    # </editor-fold>

    # <editor-fold desc="Trade & Convert">
    # This section is a bit confusing to look at. If I remember correctly, it's me completing my predecessor dev's work.
    # Most of it is handled on util.py.
    # "Convert" trades a user's Gacha unit for coins, depending on rarity.
    # "Trade" is a gacha trade offer.
    @commands.command(name="convert", aliases=["con"])
    async def convert_cmd(self, ctx, *, gacha_info):
        cards = get_gachas(ctx.author, excel_data=GACHA_DATA)  # gets user's cards
        try:
            card_id = int(gacha_info)  # checks if the data was a card id
            try:
                card = [card for card in cards if
                        card_id == card.card_id][0]  # retrieves a card with the correct id
            except IndexError:
                await ctx.send("Could not find unit.")
        except ValueError:
            try:
                card = [card for card in cards if
                        gacha_info.lower() == card.name.lower()][0]  # retrieves a card with the correct id
            except IndexError:
                await ctx.send("Could not find unit.")

        if card:  # if there is a card with the correct id
            gacha_menu = ConvertGachaMenu(ctx.author, card)  # starts a menu with the card
            await gacha_menu.start(ctx)
        else:  # if no card was found
            await ctx.send(embed=discord.Embed(title="You do not have a card with that id number.", colour=COLOR))

    @commands.command(name="trade", aliases=["traderequest"])
    async def trade_cmd(self, ctx, user: discord.Member = None, card1id=None, card2id=None):
        if user is None:
            await ctx.send("Please put in a user to trade with.")
            return
        if card1id is None:
            await ctx.send(
                f"Please put in the card you want to trade away and the card you want to receive. {PREFIX}trade @user Naruto Sasuke (or {PREFIX}trade @user 1 2)")
            return
        pool1 = get_gachas(ctx.author, GACHA_DATA)
        pool2 = get_gachas(user, GACHA_DATA)
        try:
            card_id1 = int(card1id)  # checks if the data was a card id
            card_id2 = int(card2id)
            try:
                card1 = [card for card in pool1 if
                         card_id1 == card.card_id][0]  # retrieves a card with the correct id
            except IndexError:
                await ctx.send("You don't appear to have that unit.")
                return

            try:
                card2 = [card for card in pool2 if
                         card_id2 == card.card_id][0]  # retrieves a card with the correct id
            except IndexError:
                await ctx.send("They don't appear to have that unit.")
                return
        except ValueError:
            card_name1 = card1id
            card_name2 = card2id
            try:
                card1 = [card for card in pool1 if
                         card_name1 == card.card_id][0]  # retrieves a card with the correct id
            except IndexError:
                await ctx.send("You don't appear to have that unit.")
                return

            try:
                card2 = [card for card in pool2 if
                         card_name2 == card.card_id][0]  # retrieves a card with the correct id
            except IndexError:
                await ctx.send("They don't appear to have that unit.")
                return

        original_author = ctx.author  # Apparently discord.menus doesn't have a way to register someone else's reactions
        ctx.author = user  # So we just change the "author" CTX we're giving them to trick them. Yes, really.
        await TradeConfirmMenu(original_author, card1, card2).start(ctx)

    # </editor-fold>

    # <editor-fold desc="Show">
    @commands.command(name="show", aliases=["s"])
    async def show_cmd(self, ctx, gacha_info):
        pool = get_pool('all')
        try:
            card_id = int(gacha_info)  # checks if the data was a card id
            try:
                card = [card for card in pool if
                        card_id == card.card_id][0]  # retrieves a card with the correct id
            except IndexError:
                await ctx.send("Could not find unit.")
        except ValueError:
            card_name = gacha_info
            try:
                card = [card for card in pool if
                        card_name.lower() == card.name.lower()][0]  # retrieves a card with the correct id
            except IndexError:
                await ctx.send("Could not find unit.")

        owners = []
        with open("UtilityFiles/user_info.json", "r+") as f:
            stored_info = json.load(f)
        for userid in stored_info:
            if str(card.card_id) in stored_info[userid]["gachas"].keys():
                owners.append(userid)
        if not owners:
            embed = discord.Embed(title=f"Nobody owns this card.", colour=COLOR)
        else:
            message = '>\n<@'.join(owners)
            message = ''.join(('<@', message, '>'))
            embed = discord.Embed(title=f"Number of people who own this unit: {len(owners)}", colour=COLOR)
            embed.add_field(name="Owners:", value=message, inline=True)
            await ctx.send(embed=embed)

        gacha_menu = ShowGachaMenu(card)  # starts a menu with the card
        await gacha_menu.start(ctx)

    # </editor-fold>

    # <editor-fold desc="Roll">
    @commands.command(name="roll", aliases=["r"])
    async def roll_cmd(self, ctx, rarity=None):
        """Uses a ticket and rolls to try to get another card!"""
        inventory = get_inventory(str(ctx.author.id))  # gets the user's inventory
        if rarity is None:  # checks if it's a regular roll, or if not, which rarity it is
            rarity = "tickets"
        elif rarity == 'special':
            rarity = "special_tickets"
        elif rarity == 'super':
            rarity = "super_tickets"
        elif rarity == 'ultra':
            rarity = "ultra_tickets"

        else:
            ctx.message.channel.send(
                f"Rarity not recognized. Please use one of these: \"{PREFIX}roll special/super/ultra\" (Or leave empty for normal roll)")

        if inventory[rarity] >= 1:
            pool = get_pool(rarity)  # retrieves the pool of possible cards to receive
            card = random.choice(pool)  # picks a random card from the pool
            gachas = inventory["gachas"]  # retrieves the user's gachas
            add_card(ctx.author, str(card.card_id))  # adds a new card to the gachas
            # finds out how many of the card the user now has
            if str(card.card_id) in gachas.keys():  # if the user has the card already
                card.amount = gachas[
                                  str(card.card_id)] + 1  # card.amount is set to how many of the card the user now has
                message = f"Congratulations, you just got another {card.name}! You now have {card.amount} {card.name}'s"
            else:  # the card must be new
                card.amount = 1  # the amount is by default 1
                message = f"Congratulations, you just got a new card, {card.name}!"

            # subtracts 1 ticket (Of the respective kind)
            with open("UtilityFiles/user_info.json", "r+") as f:
                stored_info = json.load(f)
                stored_info[str(ctx.author.id)][rarity] -= 1
                stored_info[str(ctx.author.id)]["rolls"] += 1
                dump_data(data=stored_info, file=f)

            await ctx.send(embed=discord.Embed(title=message, colour=COLOR))
            await ShowGachaMenu(card).start(ctx)  # creates a menu to show the card

            achievement_checker(ctx.author, "unitadd", card)  # Checks achievements
        else:
            await ctx.send(
                embed=discord.Embed(title='You do not have enough tickets to roll for a card.', colour=COLOR))

    # A copy of !roll, but it uses all tickets instead of just une.
    @commands.command(name="rollall")
    async def rollall_cmd(self, ctx, rarity=None):
        """Uses all tickets and rolls to try to get another card!"""
        inventory = get_inventory(str(ctx.author.id))  # gets the user's inventory
        if rarity is None:  # checks if it's a regular roll, or if not, which rarity it is
            rarity = "tickets"
        elif rarity == 'special':
            rarity = "special_tickets"
        elif rarity == 'super':
            rarity = "super_tickets"
        elif rarity == 'ultra':
            rarity = "ultra_tickets"
        else:
            ctx.message.channel.send(
                f"Rarity not recognized. Please use one of these: \"{PREFIX}roll special/super/ultra\" (Or leave empty for normal roll)")
        pool = get_pool(rarity)
        gachas = inventory["gachas"]  # retrieves the user's gachas
        ticketn = inventory[rarity]
        rolln = inventory['rolls']
        while ticketn > 0:
            ticketn -= 1
            rolln -= 1
            card = random.choice(pool)  # picks a random card from the pool
            add_card(ctx.author, str(card.card_id))  # adds a new card to the gachas
            # finds out how many of the card the user now has
            if str(card.card_id) in gachas.keys():  # if the user has the card already
                card.amount = gachas[
                                  str(card.card_id)] + 1  # card.amount is set to how many of the card the user now has
                message = f"Congratulations, you just got another {card.name}! You now have {card.amount} {card.name}'s"
            else:  # the card must be new
                card.amount = 1  # the amount is by default 1
                message = f"Congratulations, you just got a new card, {card.name}!"
            await ctx.send(embed=discord.Embed(title=message, colour=COLOR))
            await ShowGachaMenu(card).start(ctx)  # creates a menu to show the card
            # subtracts x tickets
        await ctx.send(embed=discord.Embed(title=f"Finished rolling {inventory[rarity]} times.", colour=COLOR))
        with open("UtilityFiles/user_info.json", "r+") as f:
            stored_info = json.load(f)
            stored_info[str(ctx.author.id)][rarity] = ticketn
            stored_info[str(ctx.author.id)]["rolls"] += rolln
            dump_data(data=stored_info, file=f)

    # </editor-fold>


def setup(bot):
    bot.add_cog(GachaGame(bot))
