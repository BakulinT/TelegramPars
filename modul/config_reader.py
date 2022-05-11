import configparser

def load_config(path=""):
	global pathDir
	config = configparser.ConfigParser()
	config.read(path+ r"/info/bot.ini")
	return config["tel_bot"]