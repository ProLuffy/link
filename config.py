# +++ Made By Obito [telegram username: @i_killed_my_clan] +++ #
import os
from os import environ
import logging
from logging.handlers import RotatingFileHandler

# Recommended
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "8065030679:AAFGbpVsYJC9TQ4b7TdKE9QfsECUJtkl2cs")
APP_ID = int(os.environ.get("APP_ID", "20718334"))
API_HASH = os.environ.get("API_HASH", "4e81464b29d79c58d0ad8a0c55ece4a5")

# Main
OWNER_ID = int(os.environ.get("OWNER_ID", "5585016974"))
PORT = os.environ.get("PORT", "8010")

# Database
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://spxsolo:umaid2008@cluster0.7fbux.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DATABASE_NAME", "Cluster0")

# Default
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

# Messages
START_MSG = os.environ.get("START_MESSAGE", "<b><blockquote expandable>Welcome to the Advanced Links Sharing Bot. With this bot, you can share links and keep your channels safe from copyright issues.</b>")
HELP = os.environ.get("HELP_MESSAGE", "<b><blockquote expandable>» Creator: <a href=https://t.me/_i_killed_my_clan>Obito</a>\n» Our Community: <a href=https://t.me/society_network>Society Network</a>\n» Anime Channel: <a href=https://t.me/animes_crew>Anime Crew</a>\n» Ongoing Anime: <a href=https://t.me/Ongoing_Crew>Ongoing Crew</a>\n» Developer: <a href=https://t.me/i_killed_my_clan>Obito</a></b>")
ABOUT = os.environ.get("ABOUT_MESSAGE", "<b><blockquote expandable>This bot is developed by Obito (@i_killed_my_clan) to securely share Telegram channel links with temporary invite links, protecting your channels from copyright issues.</b>")

try:
    ADMINS = []
    for x in (os.environ.get("ADMINS", "5585016974").split()):
        ADMINS.append(int(x))
except ValueError:
    raise Exception("Your Admins list does not contain valid integers.")

# Admin == OWNER_ID
ADMINS.append(OWNER_ID)
ADMINS.append(6497757690)

# Default
BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = None

# Logging
LOG_FILE_NAME = "links-sharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
