import codecs
import configparser

config = configparser.ConfigParser()

config.read_file(codecs.open('config.ini', "r", "utf8"))

token = config['SETTINGS']['token'].strip()
prefix = config['SETTINGS']['prefix'].strip()
COLOR = int(config['SETTINGS']['color'].strip()[2:], base=16)  # converts the color to hexadecimal
