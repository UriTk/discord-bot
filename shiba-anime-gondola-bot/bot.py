"""NOTES:
This bot is horribly unoptimized, grabbing stuff from all three APIs differently.
In reality it shouldn't need these many libraries, there's only that many because...
...I wrote three parts of the code separately and then merged them but hey...
...since python makes it easy to just use libraries right off the back, I didn't bother with optimization.
Sorry if you're actually trying to run this! You've got like, 6 pip commands ahead of you.
Also, this wont work in versions above python 3.6, thanks to discord.py being stinky.
All in all, this code could be a lot better if it *wasn't* python, but I wanted an excuse to code in Python, and here you have it.
also fuck pybooru it made my life hell due to my incompetence
Originally ran as 'py -3.6 start.py'
"""
#Personal note to the guy I'm sharing this to: The actual thing you want to see is down at the bottom.

import discord
from discord.ext import commands
import requests
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import urllib
from io import BytesIO

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7' #This is just a variable for ease of use later on.
PREFIX = "$"#*Our* prefix, viva communism.

client = commands.Bot(PREFIX)

@client.event#When bot launches
async def on_ready():
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n~~~~~~~~~~COOL DUMB BOT 3.0 start.~~~~~~~~~~\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print("Logged in as: {}".format(client.user.name))
    await client.change_presence(activity=discord.Game(name="with Uri. Prefix is $ btw."))          #Sets status

# <editor-fold desc="Gondola">
@client.command(brief="Gives a random gondola webm when you use it.",\
        name="gondola", aliases=("gondolas", "g"))
async def gondola(ctx):
    request = requests.get('https://gondola.stravers.net/random-raw', allow_redirects=False)        #gets the page and grabs...
    header = request.headers['Location']                                                            #...the redirected page, our webm.
    await ctx.message.channel.send("https://gondola.stravers.net" + header)        #Sends the webm url to gondola channel
    print ("____GONDOLA____\nServer:", ctx.message.guild, "\nUsername:", ctx.message.author)        #Prints out that X person requested gondola in Y server.
# </editor-fold>

# <editor-fold desc="Shiba  ">
@client.command(brief="Gives a random shiba png when you use it.",\
                name="shiba", aliases=("shibas", "s"))#SHIBA
async def shiba(ctx):
    request = requests.get("http://shibe.online/api/shibes?count=1&urls=true&httpsUrls=true")       #Get the content of the page, which will just be a direct RAW link to our shiba image
    await ctx.message.channel.send(request.text[2:-2])
    print ("____SHIBA____\nServer:", ctx.message.guild, "\nUsername:", ctx.message.author)
# </editor-fold>

# <editor-fold desc="Anime">
@client.command(brief=f"Gives a random post from sakugabooru, mostly animations, when you summon it. You can also use tags with it.\nExample: {PREFIX}anime cowboy_bebop",\
                name="anime", aliases=("animes", "a"))
async def anime(ctx, tag=''):
    url = 'https://www.sakugabooru.com/post.xml?tags=order%3Arandom+'+tag+';limit=1'
    headers={'User-Agent':user_agent,}                                                              #Sets an user-agent header up so the request thinks we're using a normal browser...
    request = urllib.request.Request(url,None,headers)                                              #...this is to avoid a Forbidden HTML error once we actually make our request.
    response = urllib.request.urlopen(request)                                                      #Actually opens our request...
    text = response.read()                                                                          #...and then reads it...
    soup = BeautifulSoup(text,'xml')                                                                #...and parses the xml so we can actually use it.
    try:                                                                                            #check if tag is valid
        await ctx.message.channel.send(soup.find('post')['file_url']+'\n'+soup.find('post')['tags'].replace(" ", " ||- -|| "))     #The important part here is   soup.find('post')['file_url']   , which is the part that actually grabs the direct URL of the animation.
        print ("____ANIME____\nServer:", ctx.message.guild, "\nUsername:", ctx.message.author, "\nTag:", tag)                                     #Prints out that X person requested anime in Y server, and what tags hey used if any.
    except TypeError:                                                                               #if tag wasnt valid put out an error message and make fun of the guy who tripped it in the privacy of your own house, because if they find out you're making fun of them they might dislike you.
        print ("____ANIME_invalid_tag_lamo_\nServer:", ctx.message.guild, "\nUsername:", ctx.message.author, "\nTag:", tag)                       #Same as previous print, but makes fun of the user in the console so I can bully them personally later if need be.
        await ctx.message.channel.send("Nice one. That's not a valid tag.")
# </editor-fold>

client.run('TOKEN ID')