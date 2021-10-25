import discord
from discord.ext import commands
import asyncio
from bs4 import BeautifulSoup
import requests

client = commands.Bot("!") #The bot's prefix. You can change this to any character.

@client.event#When bot launches
async def on_ready():   
    print("Hashtag Bot Started".format(client.user.name))#The message that pops in on the CMD
    #This next line is optional. It changes the bot's "Status". I generally like to use it to tell users how to use the bot. If you don't want it, you can simply delete it. It won't mess anything up.
    await client.change_presence(activity=discord.Game(name="!hashtag"))

#If you want to change what the user needs to input to trigger the command, you can either change 'name = "hashtag"' to 'name = "example"', or add it on the aliases 
#(i.e. aliases = ["test1", "test2", "h"] will make the bot run this when people use !test1, !test2 and!$h on top of the normal $hashtag.
@client.command(name = "hashtag", aliases = ["h"])
async def hashtagcmd(ctx, hashtag = None):
    """Searches best-hashtags.com for related hashtags"""
    if hashtag is None:#If the user didn't input any hashtag in, tell them to do so. If they did, proceed.
        await ctx.message.channel.send("Please put a hashtag when you use the command. For instance, \"!hashtag weed\"")
    else:
        request = requests.get('https://best-hashtags.com/hashtag/' + hashtag.lower(), allow_redirects=False)   #Gets the page and grabs all of the content.
        soup = BeautifulSoup(request.content, 'html.parser')    #Parses the HTML into something we can read
        result = soup.find(class_='tag-box tag-box-v3 margin-bottom-40')    #Finds the exact part we want to extract.
        try:                    #Attempts to send the results we've extracted.
            await ctx.message.channel.send(f"```{result.text[2:]}```**-Powered by www.twitter.com/BestStonerGuy**")
        except AttributeError:  #If the code fails to overall find any hashtags, inform the user.
            await ctx.message.channel.send(f"Couldn't find any hashtags for \"{hashtag}\"")
    
client.run('TOKEN ID')#Your Discord Bot's Token ID goes here.