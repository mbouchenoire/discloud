import datetime
import logging
import asyncio
import configparser
import schedule
import discord
from settings import MeasurementSystem, HomeSettings
from weather import Weather, WeatherForecast, WeatherServiceLocator

OWM_CONFIG_PATH = "config/open_weather_map.ini"

SMALL_CHARS = "tifjl1"
BIG_CHARS = "AMT"
DOUBLE_CHARS = "W"


def get_offset_needed(text: str) -> int:
    offset = 0

    for c in SMALL_CHARS:
        offset += text.count(c)

    for c in BIG_CHARS:
        offset -= text.count(c)

    for c in DOUBLE_CHARS:
        offset -= text.count(c) * 3

    return offset


def get_temperature_suffix(measurement_system: MeasurementSystem) -> str:
    if measurement_system is MeasurementSystem.METRIC:
        return "°C"
    elif measurement_system is MeasurementSystem.IMPERIAL:
        return "°F"
    else:
        raise ValueError("measurement system must be either metric or imperial")


def get_wind_speed_suffix(measurement_system: MeasurementSystem) -> str:
    if measurement_system is MeasurementSystem.METRIC:
        return " kmh"
    elif measurement_system is MeasurementSystem.IMPERIAL:
        return " mph"


class SendWeatherDiscordCommand(object):
    def __init__(self,
                 discord_client: discord.Client,
                 channel: discord.Channel,
                 home_settings: HomeSettings,
                 weather: Weather) -> None:
        self._discord_client = discord_client
        self._channel = channel
        self._home_settings = home_settings
        self._weather = weather

    async def execute(self) -> None:
        config = configparser.ConfigParser()
        config.read(OWM_CONFIG_PATH)

        is_home = self._home_settings.display_name.upper() == self._weather.location.upper()

        header = "" if is_home else "** -- Weather @ " + self._weather.location.title() + "**: "
        discord_icon_code = config["discord-icons"][str(self._weather.weather_code)]
        temperature_suffix = get_temperature_suffix(self._weather.measurement_system)
        wind_speed_suffix = get_wind_speed_suffix(self._weather.measurement_system)

        msg = "{}:{}:   {}{}   {}%   {}{}".format(header,
                                                  discord_icon_code,
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
            week_day = weather.date.strftime("%A")[:3] + "."
            day = weather.date.strftime("%d")
            month = weather.date.strftime("%B")[:3] + "."
            full_date = (week_day + " " + day + " " + month)

            standard_full_date_rjust = 17
            full_date_rjust = standard_full_date_rjust + get_offset_needed(full_date)
            full_date = full_date.rjust(full_date_rjust)

            discord_icon_code = config["discord-icons"][str(weather.weather_code)]
            temperature_suffix = get_temperature_suffix(weather.measurement_system)
            humidity_suffix = "%"
            wind_speed_suffix = get_wind_speed_suffix(weather.measurement_system)

            str_temperature = str(round(weather.temperature))
            str_humidity = str(weather.humidity)
            str_wind_speed = str(round(weather.wind_speed))

            temperature_rjust = 3 + len(temperature_suffix) + get_offset_needed(str_temperature)
            humidity_rjust = 3 + len(humidity_suffix) + get_offset_needed(str_humidity)
            wind_speed_rjust = 3 + 1 + len(wind_speed_suffix) + get_offset_needed(str_wind_speed)

            temperature = (str_temperature + temperature_suffix).ljust(temperature_rjust)
            humidity = (str_humidity + humidity_suffix).rjust(humidity_rjust)
            wind_speed = (str_wind_speed + wind_speed_suffix).rjust(wind_speed_rjust)

            msg += "{}   :{}:   {}   {}   {}\n".format(full_date, discord_icon_code, temperature, humidity, wind_speed)

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

        logging.debug("image to be used as the bot avatar: " + file_path)

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
        logging.info("handling weather command...")
        location = await self.__extract_location__(command)
        weather = self._weather_service_locator.get_weather_service().get_weather(location, self._measurement_system)
        await SendWeatherDiscordCommand(self._discord_client, command.channel, self._home_settings, weather).execute()

    async def handle_forecast(self, command) -> None:
        logging.info("handling forecast command...")
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

    def __should_send_forecast__(self, channel: discord.Channel) -> bool:
        return channel.name in self._home_settings.periodic_forecast_channels

    async def update_profile(self):
        await self._discord_client.wait_until_ready()

        while not self._discord_client.is_closed:
            try:
                logging.info("updating discord bot profile...")
                weather_service = self._weather_service_locator.get_weather_service()
                weather = weather_service.get_weather(self._home_settings.full_name, self._measurement_system)
                weather.location = self._home_settings.display_name
                await UpdateWeatherProfileDiscordCommand(self._discord_client, weather).execute()
                logging.info("discord bot profile updated successfully")
                await asyncio.sleep(WeatherDiscordService._UPDATE_PROFILE_FREQUENCY)
            except discord.HTTPException:
                logging.exception("discord bot profile update failed")

        logging.warning("discord connection has closed")

    async def update_presence(self):
        await self._discord_client.wait_until_ready()

        while not self._discord_client.is_closed:
            try:
                logging.info("updating discord bot presence...")
                weather_service = self._weather_service_locator.get_weather_service()
                weather = weather_service.get_weather(self._home_settings.full_name, self._measurement_system)
                await UpdateWeatherPresenceDiscordCommand(self._discord_client, weather).execute()
                logging.info("discord bot presence updated successfully")
                await asyncio.sleep(WeatherDiscordService._UPDATE_PRESENCE_FREQUENCY)
            except discord.HTTPException:
                logging.exception("discord bot presence update failed")

        logging.warning("discord connection has closed")

    async def send_home_forecast(self) -> None:
        def __periodically_send_morning_forecast__():
            __send_home_forecast__("sending periodic morning weather forecast...",
                                   lambda weathers: list(filter(lambda w: w.date == datetime.date.today(), weathers)))

        def __periodically_send_evening_forecast__():
            __send_home_forecast__("sending periodic evening weather forecast...",
                                   lambda weathers: list(filter(lambda w: w.date != datetime.date.today(), weathers)))

        def __send_home_forecast__(logging_header, weathers_predicate) -> None:
            logging.info(logging_header)

            weather_service = self._weather_service_locator.get_weather_service()
            forecast = weather_service.get_forecast(self._home_settings.full_name, self._measurement_system)

            forecast.weathers = weathers_predicate(forecast.weathers)

            for channel in self._discord_client.get_all_channels():
                if self.__should_send_forecast__(channel):
                    try:
                        asyncio.get_event_loop().run_until_complete(
                            SendForecastDiscordCommand(self._discord_client, channel, forecast).execute())
                    except discord.HTTPException:
                        msg_template = "failed to send home weather forecast (@{}) to channel {}.{}"
                        msg = msg_template.format(self._home_settings.full_name, channel.server.name, channel.name)
                        logging.exception(msg)

        schedule.every(10).seconds.do(__periodically_send_morning_forecast__)

        if self._home_settings.morning_forecast_time is not None:
            schedule.every().day.at(self._home_settings.morning_forecast_time)\
                .do(__periodically_send_morning_forecast__)

        if self._home_settings.evening_forecast_time is not None:
            schedule.every().day.at(self._home_settings.evening_forecast_time)\
                .do(__periodically_send_evening_forecast__)

        while True:
            schedule.run_pending()
            await asyncio.sleep(1)
