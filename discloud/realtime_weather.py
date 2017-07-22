import logging
import configparser
import discord
from settings import HomeSettings, TemperatureSettings
from weather import OwmWeatherService


class RealTimeWeather(object):
    def __init__(self, avatar_bytes: bytearray, title: str, description: str) -> None:
        self.avatar_bytes = avatar_bytes
        self.title = title
        self.description = description


class RealTimeWeatherFactory(object):
    def create_realtime_weather(self) -> RealTimeWeather:
        pass


class OwmRealTimeWeatherFactory(RealTimeWeatherFactory):
    _CONFIG_PATH = "config/open_weather_map.ini"

    def __init__(self, owm_weather_service: OwmWeatherService,
                 home_settings: HomeSettings, temperature_settings: TemperatureSettings) -> None:
        self._owm_weather_service = owm_weather_service
        self._home_settings = home_settings
        self._temperature_settings = temperature_settings

    @staticmethod
    def __get_avatar_bytes__(weather_code) -> bytearray:
        config = configparser.ConfigParser()
        config.read(OwmRealTimeWeatherFactory._CONFIG_PATH)

        google_icon_code = config["icons"][str(weather_code)]

        f = open("images/google/{}.png".format(google_icon_code), "rb")

        try:
            avatar_bytes = f.read()
        finally:
            f.close()

        return avatar_bytes

    def create_realtime_weather(self) -> RealTimeWeather:
        weather = self._owm_weather_service.get_weather(self._home_settings.full_name)
        avatar_bytes = OwmRealTimeWeatherFactory.__get_avatar_bytes__(weather.get_weather_code())

        temperature = weather.get_temperature(self._temperature_settings.unit)["temp"]
        temperature_suffix = "°C" if self._temperature_settings.unit == "celsius" else "°F"
        description = "{}{} @ {}".format(str(int(temperature)), temperature_suffix, self._home_settings.display_name)

        return RealTimeWeather(avatar_bytes, "", description)


class RealTimeWeatherService(object):
    def __init__(self,
                 owm_weather_service: OwmWeatherService,
                 home_settings: HomeSettings,
                 temperature_settings: TemperatureSettings,
                 discord_client: discord.Client) -> None:
        self._owm_weather_service = owm_weather_service
        self._home_settings = home_settings
        self._temperature_settings = temperature_settings
        self._discord_client = discord_client

    async def update_realtime_weather(self) -> None:
        owm_realtime_weather_factory = OwmRealTimeWeatherFactory(self._owm_weather_service,
                                                                 self._home_settings,
                                                                 self._temperature_settings)

        realtime_weather = owm_realtime_weather_factory.create_realtime_weather()

        logging.info("updating discloud profile presence...")
        await self._discord_client.change_presence(game=discord.Game(name=realtime_weather.description))

        logging.info("updating discloud profile avatar...")
        await self._discord_client.edit_profile(password=None, avatar=realtime_weather.avatar_bytes)
