import os
import logging
from main import Main

def check_environment_variable(key, value):
    if not value: raise ValueError("environment variable '" + key + "' must be set")

logging.basicConfig(level=logging.INFO)

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
check_environment_variable("DISCORD_BOT_TOKEN", DISCORD_BOT_TOKEN)

DISCORD_CHANNEL_ID = os.environ["DISCORD_CHANNEL_ID"]
check_environment_variable("DISCORD_CHANNEL_ID", DISCORD_CHANNEL_ID)

OPEN_WEATHER_MAP_API_KEY = os.environ["OPEN_WEATHER_MAP_API_KEY"]
check_environment_variable("OPEN_WEATHER_MAP_API_KEY", OPEN_WEATHER_MAP_API_KEY)

Main(DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, OPEN_WEATHER_MAP_API_KEY).run()