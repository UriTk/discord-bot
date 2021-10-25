import configparser, codecs

config = configparser.ConfigParser()

config.read_file(codecs.open('config.ini', "r", "utf8"))

token = config['SETTINGS']['token'].strip()
modrole = config['SETTINGS']['modrole'].strip()
mainserver = config['SETTINGS']['mainserver'].strip()
prefix = config['SETTINGS']['prefix'].strip()
vip = config['SETTINGS']['viprole'].strip()
VIP_N = config['SETTINGS']['privilege'].strip()

defaultchannel = config['SETTINGS']['defaultchannel'].strip()
defaultemoji = config['SETTINGS']['defaultemoji'].strip()