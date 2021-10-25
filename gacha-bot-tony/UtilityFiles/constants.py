# config file made by old dev modified for rewrite
import configparser
import os, sys,codecs

#dir_path = os.path.dirname(os.path.realpath(__file__))

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

config = configparser.ConfigParser()

config.read_file(codecs.open(str(application_path)+'/config.ini', "r", "utf8"))

TOKEN = config['SETTINGS']['discordtoken'].strip()
PREFIX = config['SETTINGS']['prefix'].strip()
COLOR = int(config['SETTINGS']['color'].strip()[2:], base=16) # converts the color to hexadecimal
NO_IMAGE_URL = config['SETTINGS']['noimageurl'].strip()
RARITY_MAP = {"C":"Common","R":"Rare","SR":"Super Rare", "UR":"Ultra Rare"}
GRADES = config['SETTINGS']['grades'].strip().split(",")
CONVERT = config['SETTINGS']['convertsettings'].strip().split(",")
RARITY_VALUE = config['SETTINGS']['leaderboardsettings'].strip().split(",")
DAILY_TIME = int(config['SETTINGS']['dailytime'].strip())
ROLE = config['SETTINGS']['modrolename'].strip()

