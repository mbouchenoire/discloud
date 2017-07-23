import logging
import configparser
from settings import IntegrationSettings, HomeSettings, TemperatureSettings, ApplicationSettings
from main import Application

logging.basicConfig(level=logging.INFO)

CONFIG = configparser.ConfigParser()
CONFIG.read("config/application.ini")

DISCORD_BOT_TOKEN = CONFIG["integration"]["discord_bot_token"]
OPEN_WEATHER_MAP_API_KEY = CONFIG["integration"]["open_weather_map_api_key"]
HOME_FULL_NAME = CONFIG["home"]["full_name"]
HOME_DISPLAY_NAME = CONFIG["home"]["display_name"]
HOME_UPDATE_FREQUENCY = CONFIG["home"]["update_frequency"]
TEMPERATURE_UNIT = CONFIG["temperature"]["unit"]
TEMPERATURE_THRESHOLD_HOT = CONFIG["temperature"]["threshold_hot"]
TEMPERATURE_THRESHOLD_COLD = CONFIG["temperature"]["threshold_cold"]
TEMPERATURE_THRESHOLD_COLOR = CONFIG["temperature"]["threshold_color"]

INTEGRATION_SETTINGS = IntegrationSettings(DISCORD_BOT_TOKEN, OPEN_WEATHER_MAP_API_KEY)
HOME_SETTINGS = HomeSettings(HOME_FULL_NAME, HOME_DISPLAY_NAME, HOME_UPDATE_FREQUENCY)
TEMPERATURE_SETTINGS = TemperatureSettings(TEMPERATURE_UNIT, TEMPERATURE_THRESHOLD_HOT,
                                           TEMPERATURE_THRESHOLD_COLD, TEMPERATURE_THRESHOLD_COLOR)

APPLICATION_SETTINGS = ApplicationSettings(INTEGRATION_SETTINGS, HOME_SETTINGS, TEMPERATURE_SETTINGS)

Application(APPLICATION_SETTINGS).run()
