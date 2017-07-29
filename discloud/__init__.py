import logging
import configparser
from settings import MeasurementSystem, IntegrationSettings, HomeSettings, ApplicationSettings
from main import Application

CONFIG = configparser.ConfigParser()
CONFIG.read("config/application.ini")

LOGGING_LEVEL_STR = CONFIG["global"]["logging_level"]

if LOGGING_LEVEL_STR == "debug":
    logging.basicConfig(level=logging.DEBUG)
elif LOGGING_LEVEL_STR == "error":
    logging.basicConfig(level=logging.ERROR)
elif LOGGING_LEVEL_STR == "info":
    logging.basicConfig(level=logging.INFO)
else:
    raise ValueError("logging level must be debug/error/info")

STR_MEASUREMENT_SYSTEM = CONFIG["global"]["measurement_system"]
DISCORD_BOT_TOKEN = CONFIG["integration"]["discord_bot_token"]
OPEN_WEATHER_MAP_API_KEY = CONFIG["integration"]["open_weather_map_api_key"]
HOME_FULL_NAME = CONFIG["home"]["full_name"]
HOME_DISPLAY_NAME = CONFIG["home"]["display_name"]

MEASUREMENT_SYSTEM = MeasurementSystem.METRIC if STR_MEASUREMENT_SYSTEM == "metric" else MeasurementSystem.IMPERIAL

INTEGRATION_SETTINGS = IntegrationSettings(DISCORD_BOT_TOKEN, OPEN_WEATHER_MAP_API_KEY)
HOME_SETTINGS = HomeSettings(HOME_FULL_NAME, HOME_DISPLAY_NAME)

APPLICATION_SETTINGS = ApplicationSettings(MEASUREMENT_SYSTEM, INTEGRATION_SETTINGS, HOME_SETTINGS)

Application(APPLICATION_SETTINGS).run()
