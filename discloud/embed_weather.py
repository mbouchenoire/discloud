import datetime
import configparser
import discord
from settings import TemperatureSettings
from weather import OwmWeatherService


class EmbedWeatherFactory(object):
    def create_embed_weather(self) -> discord.Embed:
        pass


class OwmEmbedWeatherFactory(EmbedWeatherFactory):
    _CONFIG_PATH = "config/open_weather_map.ini"
    _COLORS_CONFIG_PATH = "config/colors.ini"
    _ICON_URL_TEMPLATE = "https://ssl.gstatic.com/onebox/weather/{}/{}.png"
    _ICON_SIZE = "64"

    @staticmethod
    def __weather_code_to_google_icon_url__(weather_code: int) -> str:
        config = configparser.ConfigParser()
        config.read(OwmEmbedWeatherFactory._CONFIG_PATH)

        google_icon_code = config["icons"][str(weather_code)]

        return OwmEmbedWeatherFactory._ICON_URL_TEMPLATE.format(OwmEmbedWeatherFactory._ICON_SIZE, google_icon_code)

    @staticmethod
    def __get_color__(weather_code: int, temperature_min: float, temperature_max: float,
                      temperature_settings: TemperatureSettings) -> int:

        colors = configparser.ConfigParser()
        colors.read(OwmEmbedWeatherFactory._COLORS_CONFIG_PATH)

        if temperature_min <= temperature_settings.threshold_cold \
                or temperature_max >= temperature_settings.threshold_hot:
            return int(colors["material"][temperature_settings.threshold_color], 0)

        owm_config = configparser.ConfigParser()
        owm_config.read(OwmEmbedWeatherFactory._CONFIG_PATH)

        weather_color_code = owm_config["colors"][str(weather_code)]

        return int(colors["material"][weather_color_code], 0)

    def __init__(self, owm_weather_service: OwmWeatherService, date: datetime.datetime, place: str,
                 temperature_settings: TemperatureSettings) -> None:
        self._owm_weather_service = owm_weather_service
        self._date = date
        self._place = place
        self._temperature_settings = temperature_settings

    def create_embed_weather(self) -> discord.Embed:
        is_today = self._date.date() == datetime.date.today()

        if is_today:
            weather = self._owm_weather_service.get_weather(self._place)
        else:
            weather = self._owm_weather_service.get_forecast(self._place, self._date)

        detailed_status = weather.get_detailed_status().title()
        weather_code = weather.get_weather_code()
        humidity = weather.get_humidity()
        temperature = weather.get_temperature(self._temperature_settings.unit)

        temperature_min = None
        temperature_max = None

        if "temp_min" in temperature:  # when manipulating today's weather (observation)
            temperature_min = temperature["temp_min"]
            temperature_max = temperature["temp_max"]
        elif "min" in temperature:  # when manipulating forecast
            temperature_min = temperature["min"]
            temperature_max = temperature["max"]

        temperature_suffix = "°C" if self._temperature_settings.unit == "celsius" else "°F"

        wind_speed = int(weather.get_wind()["speed"] * 3.6)
        icon_url = OwmEmbedWeatherFactory.__weather_code_to_google_icon_url__(weather_code)

        color = OwmEmbedWeatherFactory.__get_color__(weather_code, temperature_min, temperature_max,
                                                     self._temperature_settings)

        embed = discord.Embed(colour=color)
        embed.title = "{} @ {}".format(self._date.strftime("%A %d %B"), self._place.title())
        embed.description = detailed_status
        embed.add_field(name="High temp.", value=str(int(temperature_max)) + temperature_suffix)
        embed.add_field(name="Low temp.", value=str(int(temperature_min)) + temperature_suffix)
        embed.add_field(name="Humidity", value=str(humidity) + "%")
        embed.add_field(name="Wind", value=str(wind_speed) + " km/h")
        embed.set_thumbnail(url=icon_url)
        embed.set_footer(text="github.com/mbouchenoire/discloud",
                         icon_url="https://avatars6.githubusercontent.com/u/8810050?v=4&s=460")

        return embed
