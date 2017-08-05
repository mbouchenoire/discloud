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

import discord
from command import CommandHandler, WeatherDiscordService
from weather import WeatherService
from settings import ApplicationSettings
from message_factory import MessageFactory


class Application(object):
    def __init__(self, application_settings: ApplicationSettings) -> None:
        self._settings = application_settings

    def run(self) -> None:
        discord_client = discord.Client()

        weather_service = WeatherService(self._settings.integration_settings.open_weather_map_api_key,
                                         self._settings.integration_settings.weather_underground_api_key)

        message_factory = MessageFactory(self._settings)

        command_handler = CommandHandler(self._settings,
                                         weather_service,
                                         discord_client,
                                         message_factory)

        weather_discord_service = WeatherDiscordService(self._settings.measurement_system,
                                                        self._settings.home_settings,
                                                        weather_service,
                                                        discord_client)

        @discord_client.event
        async def on_message(message) -> None:
            await command_handler.handle(message)

        discord_client.loop.create_task(weather_discord_service.send_home_forecast())
        discord_client.loop.create_task(weather_discord_service.update_profile())
        discord_client.loop.create_task(weather_discord_service.update_presence())
        discord_client.run(self._settings.integration_settings.discord_bot_token)
