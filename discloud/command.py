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
from typing import List
from settings import Language, MeasurementSystem, ConcurrencyPriority, HomeSettings, ApplicationSettings
from weather import Weather, WeatherForecast, WeatherService
from message_factory import MessageFactory

OWM_CONFIG_PATH = "config/open_weather_map.ini"


class SendWeatherDiscordCommand(object):
    def __init__(self,
                 discord_client: discord.Client,
                 channel: discord.Channel,
                 home_settings: HomeSettings,
                 weather: Weather,
                 message_factory: MessageFactory) -> None:
        self._discord_client = discord_client
        self._channel = channel
        self._home_settings = home_settings
        self._weather = weather
        self._message_factory = message_factory

    async def execute(self) -> None:
        msg = self._message_factory.format_weather(self._weather)
        await self._discord_client.send_message(self._channel, msg)


class SendForecastDiscordCommand(object):
    def __init__(self,
                 discord_client: discord.Client,
                 channel: discord.Channel,
                 forecast: WeatherForecast,
                 language: Language,
                 message_factory: MessageFactory) -> None:
        self._discord_client = discord_client
        self._channel = channel
        self._forecast = forecast
        self._language = language
        self._message_factory = message_factory

    def __get_localized_weekday__(self, weekday_index: int) -> str:
        config = configparser.ConfigParser()
        config.read("i18n/{}.ini".format(self._language.value))
        return config["weekdays"][str(weekday_index)]

    async def execute(self) -> None:
        msg = self._message_factory.format_weather_forecast(self._forecast)
        await self._discord_client.send_message(self._channel, msg)


class UpdateWeatherPresenceDiscordCommand(object):
    def __init__(self, discord_client: discord.Client, weather: Weather, should_help: bool) -> None:
        self._discord_client = discord_client
        self._weather = weather
        self._should_help = should_help

    async def execute(self) -> None:
        msg = MessageFactory.format_presence(self._weather, self._should_help)
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

    def __init__(self,
                 application_settings: ApplicationSettings,
                 weather_service: WeatherService,
                 discord_client: discord.Client,
                 message_factory: MessageFactory) -> None:
        self._application_settings = application_settings
        self._weather_service = weather_service
        self._discord_client = discord_client
        self._message_factory = message_factory

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

    @staticmethod
    def __build_commands__(prefixes: List[str], commands: List[str]) -> List[str]:
        command_prefixes = list()

        for command in commands:
            for prefix in prefixes:
                command_prefixes.append(prefix + command)

        return command_prefixes

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

    def __build_weather_commands__(self) -> List[str]:
        return CommandHandler.__build_commands__(self._application_settings.command_settings.prefixes,
                                                 self._application_settings.command_settings.weather)

    def __build_forecast_commands__(self) -> List[str]:
        return CommandHandler.__build_commands__(self._application_settings.command_settings.prefixes,
                                                 self._application_settings.command_settings.forecast)

    def __build_help_commands__(self) -> List[str]:
        return CommandHandler.__build_commands__(self._application_settings.command_settings.prefixes,
                                                 self._application_settings.command_settings.help)

    def __extract_location__(self, command) -> str:
        content = command.content.replace("@ ", "@").replace("@", "")

        weather_commands = self.__build_weather_commands__()
        forecast_commands = self.__build_forecast_commands__()

        for prefix in weather_commands:
            content = content.replace(prefix, "", 1)

        for prefix in forecast_commands:
            content = content.replace(prefix, "", 1)

        if content is None or content.strip() == "":
            return self._application_settings.home_settings.full_name
        else:
            return content

    async def handle_weather(self, command) -> None:
        logging.info("handling weather command...")
        location = self.__extract_location__(command)
        weather = self._weather_service.get_weather(location, self._application_settings.measurement_system)
        await SendWeatherDiscordCommand(self._discord_client,
                                        command.channel,
                                        self._application_settings.home_settings,
                                        weather,
                                        self._message_factory).execute()

    async def handle_forecast(self, command) -> None:
        logging.info("handling forecast command...")
        location = self.__extract_location__(command)
        forecast = self._weather_service.get_forecast(location, self._application_settings.measurement_system)
        await SendForecastDiscordCommand(self._discord_client,
                                         command.channel, forecast,
                                         self._application_settings.language,
                                         self._message_factory).execute()

    async def handle_help(self, command) -> None:
        logging.info("handling help...")
        msg = MessageFactory.format_help()
        await self._discord_client.send_message(command.channel, msg)

    async def handle(self, command) -> None:
        weather_commands = self.__build_weather_commands__()
        forecast_commands = self.__build_forecast_commands__()
        help_commands = self.__build_help_commands__()

        if any(command.content.startswith(prefix) for prefix in weather_commands):
            if not CommandHandler.__is_parametized_command__(command) or self.__has_handling_priority__(command):
                return await self.handle_weather(command)

        if any(command.content.startswith(prefix) for prefix in forecast_commands):
            if not CommandHandler.__is_parametized_command__(command) or self.__has_handling_priority__(command):
                return await self.handle_forecast(command)

        if any(command.content.startswith(prefix) for prefix in help_commands):
            if True or self.__has_handling_priority__(command):
                return await self.handle_help(command)


class WeatherDiscordService(object):
    _REALTIME_WEATHER_FREQUENCY = 31 * 60  # 31 minutes
    _HELP_FREQUENCY = 1 * 60  # 1 minute

    def __init__(self,
                 measurement_system: MeasurementSystem,
                 home_settings: HomeSettings,
                 weather_service: WeatherService,
                 discord_client: discord.Client) -> None:
        self._measurement_system = measurement_system
        self._home_settings = home_settings
        self._weather_service = weather_service
        self._discord_client = discord_client

    def __should_send_forecast__(self, channel: discord.Channel) -> bool:
        return channel.name in self._home_settings.periodic_forecast_channels

    async def update_profile(self) -> None:
        await self._discord_client.wait_until_ready()

        while not self._discord_client.is_closed:
            try:
                logging.debug("updating discord bot profile...")
                weather = self._weather_service.get_weather(self._home_settings.full_name, self._measurement_system)
                weather.location = self._home_settings.display_name
                await UpdateWeatherProfileDiscordCommand(self._discord_client, weather).execute()
                logging.debug("discord bot profile updated successfully")
                await asyncio.sleep(WeatherDiscordService._REALTIME_WEATHER_FREQUENCY)
            except discord.HTTPException:
                logging.exception("discord bot profile update failed")

        logging.warning("discord connection has closed")

    async def update_presence(self) -> None:
        await self._discord_client.wait_until_ready()
        await asyncio.sleep(5)  # to mitigate concurrency problems with update_profile()

        weather = None
        should_help = False

        while not self._discord_client.is_closed:
            try:
                logging.debug("updating discord bot presence...")

                if weather is None:
                    weather = self._weather_service.get_weather(self._home_settings.full_name, self._measurement_system)
                    weather_date = datetime.datetime.now()
                else:
                    seconds_since_realtime_update = (datetime.datetime.now() - weather_date).total_seconds()

                    if seconds_since_realtime_update >= WeatherDiscordService._REALTIME_WEATHER_FREQUENCY:
                        weather = self._weather_service.get_weather(self._home_settings.full_name,
                                                                    self._measurement_system)
                        weather_date = datetime.datetime.now()

                await UpdateWeatherPresenceDiscordCommand(self._discord_client, weather, should_help).execute()
                should_help = not should_help
                logging.debug("discord bot presence updated successfully")
                await asyncio.sleep(WeatherDiscordService._HELP_FREQUENCY)
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

            forecast = self._weather_service.get_forecast(self._home_settings.full_name, self._measurement_system)

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
