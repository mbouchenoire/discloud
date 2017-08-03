# Copyright (C) 2017 discloud
#
# This file is part of discloud.
#
# discloud is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# discloud is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with discloud.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
import asyncio
import configparser
import schedule
import discord
from settings import Language, MeasurementSystem, ConcurrencyPriority, HomeSettings, ApplicationSettings
from weather import Weather, WeatherForecast, WeatherServiceLocator

OWM_CONFIG_PATH = "config/open_weather_map.ini"

SMALL_CHARS = "tifjl1"
BIG_CHARS = "ADTVm05"
DOUBLE_CHARS = "MW"


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

        header = "" if is_home else "**@ " + self._weather.location.title() + "**: "
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
    def __init__(self,
                 discord_client: discord.Client,
                 channel: discord.Channel,
                 forecast: WeatherForecast,
                 language: Language) -> None:
        self._discord_client = discord_client
        self._channel = channel
        self._forecast = forecast
        self._language = language

    def __get_localized_weekday__(self, weekday_index: int) -> str:
        config = configparser.ConfigParser()
        config.read("i18n/{}.ini".format(self._language.value))
        return config["weekdays"][str(weekday_index)]

    async def execute(self) -> None:
        config = configparser.ConfigParser()
        config.read(OWM_CONFIG_PATH)

        msg = "**@ " + self._forecast.weathers[0].location.title() + "**\n\n"

        for weather in self._forecast.weathers:
            weekday_index = weather.date.weekday()
            week_day = self.__get_localized_weekday__(weekday_index)
            day = weather.date.strftime("%d")
            full_date = (week_day + " " + day)

            standard_full_date_rjust = 11
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
    def __init__(self, discord_client: discord.Client, weather: Weather, should_promote: bool) -> None:
        self._discord_client = discord_client
        self._weather = weather
        self._should_promote = should_promote

    async def execute(self) -> None:
        temperature_suffix = get_temperature_suffix(self._weather.measurement_system)
        humidity_suffix = "%"
        wind_speed_suffix = get_wind_speed_suffix(self._weather.measurement_system)

        temperature_text = str(round(self._weather.temperature)) + temperature_suffix
        humidity_text = str(self._weather.humidity) + humidity_suffix
        wind_speed_text = str(round(self._weather.wind_speed)) + wind_speed_suffix

        if self._should_promote:
            maximum_presence_length = 15
            promotion_text = "!discloud"
            spaces = " " * (maximum_presence_length - len(temperature_text) - len(promotion_text))
            msg = "{}{}{}".format(temperature_text, spaces, promotion_text)
        else:
            msg = "{}  {}  {}".format(temperature_text, humidity_text, wind_speed_text)

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

    def __init__(self, discord_client: discord.Client, weather: Weather) -> None:
        self._discord_client = discord_client
        self._weather = weather

    async def execute(self) -> None:
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

    _VALID_HELP_PREFIXES = ["!discloud", "discloud", "!bots", "!bot", "weatherbot", "botweather"]

    def __init__(self,
                 application_settings: ApplicationSettings,
                 weather_service_locator: WeatherServiceLocator,
                 discord_client: discord.Client) -> None:
        self._application_settings = application_settings
        self._weather_service_locator = weather_service_locator
        self._discord_client = discord_client

    @staticmethod
    def __is_discloud_bot__(member: discord.Member) -> bool:
        if member.game is None:
            return False

        bot_game_probable_strings = ["°C", "°F", "%", "mph", "kmh", "discloud"]
        bot_strings_threshold = 2

        member_found_strings = 0

        for probable_string in bot_game_probable_strings:
            if probable_string in member.game.name:
                member_found_strings += 1

        return member_found_strings >= bot_strings_threshold

    @staticmethod
    def __is_parametized_command__(command) -> bool:
        return len(command.content.split(" ")) > 1

    def __has_handling_priority__(self, command) -> bool:
        # Currently, the bot with the lowest ID detains the handling priority

        if self._application_settings.concurrency_priority is ConcurrencyPriority.ALWAYS:
            return True
        elif self._application_settings.concurrency_priority is ConcurrencyPriority.NEVER:
            return False

        for member in command.channel.server.members:
            if CommandHandler.__is_discloud_bot__(member) and member.status is discord.Status.online:
                if member.id < self._discord_client.user.id:
                    return False

        return True

    def __extract_location__(self, command) -> str:
        content = command.content.replace("@ ", "@").replace("@", "")

        for prefix in CommandHandler._VALID_WEATHER_PREFIXES:
            content = content.replace(prefix, "", 1)

        for prefix in CommandHandler._VALID_FORECAST_PREFIXES:
            content = content.replace(prefix, "", 1)

        if content is None or content.strip() == "":
            return self._application_settings.home_settings.full_name
        else:
            return content

    async def handle_weather(self, command) -> None:
        logging.info("handling weather command...")
        location = self.__extract_location__(command)
        weather_service = self._weather_service_locator.get_weather_service()
        weather = weather_service.get_weather(location, self._application_settings.measurement_system)
        await SendWeatherDiscordCommand(self._discord_client,
                                        command.channel,
                                        self._application_settings.home_settings,
                                        weather).execute()

    async def handle_forecast(self, command) -> None:
        logging.info("handling forecast command...")
        location = self.__extract_location__(command)
        weather_service = self._weather_service_locator.get_weather_service()
        forecast = weather_service.get_forecast(location, self._application_settings.measurement_system)
        await SendForecastDiscordCommand(self._discord_client,
                                         command.channel, forecast,
                                         self._application_settings.language).execute()

    async def handle_help(self, command) -> None:
        logging.info("handling help...")
        await self._discord_client.send_message(command.channel, "http://github.com/mbouchenoire/discloud")

    async def handle(self, command) -> None:
        if any(command.content.startswith(prefix) for prefix in CommandHandler._VALID_WEATHER_PREFIXES):
            if not CommandHandler.__is_parametized_command__(command) or self.__has_handling_priority__(command):
                return await self.handle_weather(command)

        if any(command.content.startswith(prefix) for prefix in CommandHandler._VALID_FORECAST_PREFIXES):
            if not CommandHandler.__is_parametized_command__(command) or self.__has_handling_priority__(command):
                return await self.handle_forecast(command)

        if any(command.content.startswith(prefix) for prefix in CommandHandler._VALID_HELP_PREFIXES):
            if self.__has_handling_priority__(command):
                return await self.handle_help(command)


class WeatherDiscordService(object):
    _UPDATE_PROFILE_FREQUENCY = 31 * 60  # 31 minutes
    _UPDATE_PRESENCE_FREQUENCY = 60  # 1 minute

    def __init__(self,
                 measurement_system: MeasurementSystem,
                 home_settings: HomeSettings,
                 weather_service_locator: WeatherServiceLocator,
                 discord_client: discord.Client) -> None:
        self._measurement_system = measurement_system
        self._home_settings = home_settings
        self._weather_service_locator = weather_service_locator
        self._discord_client = discord_client

    def __should_send_forecast__(self, channel: discord.Channel) -> bool:
        return channel.name in self._home_settings.periodic_forecast_channels

    async def update_profile(self) -> None:
        await self._discord_client.wait_until_ready()

        while not self._discord_client.is_closed:
            try:
                logging.debug("updating discord bot profile...")
                weather_service = self._weather_service_locator.get_weather_service()
                weather = weather_service.get_weather(self._home_settings.full_name, self._measurement_system)
                weather.location = self._home_settings.display_name
                await UpdateWeatherProfileDiscordCommand(self._discord_client, weather).execute()
                logging.info("discord bot profile updated successfully")
                await asyncio.sleep(WeatherDiscordService._UPDATE_PROFILE_FREQUENCY)
            except discord.HTTPException:
                logging.exception("discord bot profile update failed")

        logging.warning("discord connection has closed")

    async def update_presence(self) -> None:
        await self._discord_client.wait_until_ready()

        should_promote = False

        while not self._discord_client.is_closed:
            try:
                logging.debug("updating discord bot presence...")
                weather_service = self._weather_service_locator.get_weather_service()
                weather = weather_service.get_weather(self._home_settings.full_name, self._measurement_system)
                await UpdateWeatherPresenceDiscordCommand(self._discord_client, weather, should_promote).execute()
                should_promote = not should_promote
                logging.info("discord bot presence updated successfully")
                await asyncio.sleep(WeatherDiscordService._UPDATE_PRESENCE_FREQUENCY)
            except discord.HTTPException:
                logging.exception("discord bot presence update failed")

        logging.warning("discord connection has closed")

    async def send_home_forecast(self) -> None:
        def __periodically_send_morning_forecast__() -> None:
            __send_home_forecast__("sending periodic morning weather forecast...",
                                   lambda weathers: list(filter(lambda w: w.date == datetime.date.today(), weathers)))

        def __periodically_send_evening_forecast__() -> None:
            __send_home_forecast__("sending periodic evening weather forecast...",
                                   lambda weathers: list(filter(lambda w: w.date != datetime.date.today(), weathers)))

        def __send_home_forecast__(logging_header: str, weathers_predicate) -> None:
            logging.debug(logging_header)

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

        if self._home_settings.morning_forecast_time is not None:
            schedule.every().day.at(self._home_settings.morning_forecast_time)\
                .do(__periodically_send_morning_forecast__)

        if self._home_settings.evening_forecast_time is not None:
            schedule.every().day.at(self._home_settings.evening_forecast_time)\
                .do(__periodically_send_evening_forecast__)

        while True:
            schedule.run_pending()
            await asyncio.sleep(1)
