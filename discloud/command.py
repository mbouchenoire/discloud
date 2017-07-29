import asyncio
import configparser
import discord
from settings import MeasurementSystem, HomeSettings
from weather import Weather, WeatherForecast, WeatherServiceLocator

OWM_CONFIG_PATH = "config/open_weather_map.ini"


def get_temperature_suffix(measurement_system: MeasurementSystem) -> str:
    if measurement_system is MeasurementSystem.METRIC:
        return "°C"
    elif measurement_system is MeasurementSystem.IMPERIAL:
        return "°F"
    else:
        raise ValueError("measurement system must be either metric or imperial")


def get_wind_speed_suffix(measurement_system: MeasurementSystem) -> str:
    if measurement_system is MeasurementSystem.METRIC:
        return " km/h"
    elif measurement_system is MeasurementSystem.IMPERIAL:
        return " mph"


class SendWeatherDiscordCommand(object):
    def __init__(self, discord_client: discord.Client, channel: discord.Channel, weather: Weather) -> None:
        self._discord_client = discord_client
        self._channel = channel
        self._weather = weather

    async def execute(self) -> None:
        config = configparser.ConfigParser()
        config.read(OWM_CONFIG_PATH)

        discord_icon_code = config["discord-icons"][str(self._weather.weather_code)]
        temperature_suffix = get_temperature_suffix(self._weather.measurement_system)
        wind_speed_suffix = get_wind_speed_suffix(self._weather.measurement_system)

        msg = ":{}:   {}{}   {}%   {} {}".format(discord_icon_code,
                                                 round(self._weather.temperature), temperature_suffix,
                                                 self._weather.humidity,
                                                 round(self._weather.wind_speed), wind_speed_suffix)

        await self._discord_client.send_message(self._channel, msg)


class SendForecastDiscordCommand(object):
    def __init__(self, discord_client: discord.Client, channel: discord.Channel, forecast: WeatherForecast):
        self._discord_client = discord_client
        self._channel = channel
        self._forecast = forecast

    async def execute(self):
        config = configparser.ConfigParser()
        config.read(OWM_CONFIG_PATH)

        msg = "**Weather Forecast @ " + self._forecast.weathers[0].location.title() + "**\n\n"

        for weather in self._forecast.weathers:
            discord_icon_code = config["discord-icons"][str(weather.weather_code)]
            temperature_suffix = get_temperature_suffix(weather.measurement_system)
            humidity_suffix = "%"
            wind_speed_suffix = get_wind_speed_suffix(weather.measurement_system)

            str_temperature = str(round(weather.temperature))
            str_humidity = str(weather.humidity)
            str_wind_speed = str(round(weather.wind_speed))

            temperature_rjust = 3 + len(temperature_suffix) + str_temperature.count("1")
            humidity_rjust = 3 + len(humidity_suffix) + str_humidity.count("1")
            wind_speed_rjust = 3 + 1 + len(wind_speed_suffix) + str_wind_speed.count("1")

            date = weather.date.strftime("%A %d %B")
            temperature = (str_temperature + temperature_suffix).rjust(temperature_rjust)
            humidity = (str_humidity + humidity_suffix).rjust(humidity_rjust)
            wind_speed = (str_wind_speed + wind_speed_suffix).rjust(wind_speed_rjust)

            msg += "{}   :{}:   {}   {}   {}\n".format(date, discord_icon_code, temperature, humidity, wind_speed)

        await self._discord_client.send_message(self._channel, msg)


class UpdateWeatherPresenceDiscordCommand(object):
    def __init__(self, discord_client: discord.Client, weather: Weather):
        self._discord_client = discord_client
        self._weather = weather

    async def execute(self):
        temperature_suffix = get_temperature_suffix(self._weather.measurement_system)
        wind_speed_suffix = get_wind_speed_suffix(self._weather.measurement_system)

        msg = "{}{}  {}%  {} {}".format(round(self._weather.temperature), temperature_suffix,
                                        self._weather.humidity,
                                        round(self._weather.wind_speed), wind_speed_suffix)

        await self._discord_client.change_presence(game=discord.Game(name=msg))


class UpdateWeatherProfileDiscordCommand(object):
    @staticmethod
    def __get_avatar_bytes__(weather_code) -> bytearray:
        config = configparser.ConfigParser()
        config.read(OWM_CONFIG_PATH)

        google_icon_code = config["google-icons"][str(weather_code)]

        file_path = "images/google/{}.png".format(google_icon_code)

        f = open(file_path, "rb")

        try:
            avatar_bytes = f.read()
        finally:
            f.close()

        return avatar_bytes

    def __init__(self, discord_client: discord.Client, weather: Weather):
        self._discord_client = discord_client
        self._weather = weather

    async def execute(self):
        avatar_bytes = UpdateWeatherProfileDiscordCommand.__get_avatar_bytes__(self._weather.weather_code)
        await self._discord_client.edit_profile(password=None, username=self._weather.location, avatar=avatar_bytes)


class CommandHandler(object):
    _INVALID_WEATHER_COMMAND_FORMAT_MSG = "invalid weather command format (should be '!weather Paris')"
    _INVALID_OSSET_MSG = "the forecast daily offset must be >= 0"

    _VALID_WEATHER_PREFIXES = ["!weather", "weather",
                               "!météo", "météo",
                               "!meteo", "meteo"]

    _VALID_FORECAST_PREFIXES = ["!forecast", "forecast",
                                "!prévisions", "prévisions",
                                "!previsions", "previsions",
                                "!prévision", "prévision",
                                "!prevision", "prevision",
                                "!prév", "!prev"]

    def __init__(self,
                 measurement_system: MeasurementSystem,
                 home_settings: HomeSettings,
                 weather_service_locator: WeatherServiceLocator,
                 discord_client: discord.Client):
        self._measurement_system = measurement_system
        self._home_settings = home_settings
        self._weather_service_locator = weather_service_locator
        self._discord_client = discord_client

    async def __extract_location__(self, command) -> str:
        parts = command.content.replace("@ ", "@").split(" ")

        if len(parts) >= 2:
            location = parts[1]
            location = location.replace("@", "")
        else:
            location = self._home_settings.full_name

        return location

    async def handle_weather(self, command) -> None:
        location = await self.__extract_location__(command)
        weather = self._weather_service_locator.get_weather_service().get_weather(location, self._measurement_system)
        await SendWeatherDiscordCommand(self._discord_client, command.channel, weather).execute()

    async def handle_forecast(self, command) -> None:
        location = await self.__extract_location__(command)
        forecast = self._weather_service_locator.get_weather_service().get_forecast(location, self._measurement_system)
        await SendForecastDiscordCommand(self._discord_client, command.channel, forecast).execute()

    async def handle(self, command) -> None:
        if any(command.content.startswith(prefix) for prefix in CommandHandler._VALID_WEATHER_PREFIXES):
            return await self.handle_weather(command)

        if any(command.content.startswith(prefix) for prefix in CommandHandler._VALID_FORECAST_PREFIXES):
            return await self.handle_forecast(command)


class WeatherDiscordService(object):
    _UPDATE_PROFILE_FREQUENCY = 31 * 60  # 31 minutes
    _UPDATE_PRESENCE_FREQUENCY = 15 * 60  # 15 minutes

    def __init__(self,
                 measurement_system: MeasurementSystem,
                 home_settings: HomeSettings,
                 weather_service_locator: WeatherServiceLocator,
                 discord_client: discord.Client):
        self._measurement_system = measurement_system
        self._home_settings = home_settings
        self._weather_service_locator = weather_service_locator
        self._discord_client = discord_client

    async def update_profile(self):
        await self._discord_client.wait_until_ready()

        while not self._discord_client.is_closed:
            weather_service = self._weather_service_locator.get_weather_service()
            weather = weather_service.get_weather(self._home_settings.full_name, self._measurement_system)
            await UpdateWeatherProfileDiscordCommand(self._discord_client, weather).execute()
            await asyncio.sleep(WeatherDiscordService._UPDATE_PROFILE_FREQUENCY)

    async def update_presence(self):
        await self._discord_client.wait_until_ready()

        while not self._discord_client.is_closed:
            weather_service = self._weather_service_locator.get_weather_service()
            weather = weather_service.get_weather(self._home_settings.full_name, self._measurement_system)
            await UpdateWeatherPresenceDiscordCommand(self._discord_client, weather).execute()
            await asyncio.sleep(WeatherDiscordService._UPDATE_PRESENCE_FREQUENCY)
