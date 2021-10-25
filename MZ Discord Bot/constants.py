import configparser
import os, sys,codecs

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

config = configparser.ConfigParser()

config.read_file(codecs.open(str(application_path)+'/config.ini', "r", "utf8"))

TOKEN = config['SETTINGS']['discordtoken'].strip()
PREFIX = config['SETTINGS']['prefix'].strip()
EMAIL = config['SETTINGS']['email'].strip()
PASS = config['SETTINGS']['pass'].strip()
ROLE5 = config['SETTINGS']['master'].strip()
ROLE4 = config['SETTINGS']['diamond'].strip()
ROLE3 = config['SETTINGS']['plat'].strip()
ROLE2 = config['SETTINGS']['gold'].strip()
ROLE1 = config['SETTINGS']['silver'].strip()
ROLE0 = config['SETTINGS']['bronze'].strip()
