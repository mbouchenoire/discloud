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

from enum import Enum
from typing import List


class MeasurementSystem(Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"


class ConcurrencyPriority(Enum):
    ALWAYS = "always"
    AUTO = "auto"
    NEVER = "never"


class Language(Enum):
    ENGLISH = "en"
    RUSSIAN = "ru"
    JAPANESE = "jp"
    GERMAN = "de"
    SPANISH = "es"
    FRENCH = "fr"


class IntegrationSettings(object):
    def __init__(self, discord_bot_token: str, open_weather_map_api_key: str) -> None:
        self.discord_bot_token = discord_bot_token
        self.open_weather_map_api_key = open_weather_map_api_key


class HomeSettings(object):
    def __init__(self,
                 full_name: str,
                 display_name: str,
                 periodic_forecast_channels: List[str],
                 morning_forecast_time: str,
                 evening_forecast_time: str) -> None:
        self.full_name = full_name
        self.display_name = display_name
        self.periodic_forecast_channels = periodic_forecast_channels

        if morning_forecast_time is None or morning_forecast_time.strip() == "":
            self.morning_forecast_time = None
        else:
            self.morning_forecast_time = morning_forecast_time

        if evening_forecast_time is None or evening_forecast_time.strip() == "":
            self.evening_forecast_time = None
        else:
            self.evening_forecast_time = evening_forecast_time


class ApplicationSettings(object):
    def __init__(self,
                 logging_level: int,
                 language: Language,
                 measurement_system: MeasurementSystem,
                 concurrency_priority: ConcurrencyPriority,
                 integration_settings: IntegrationSettings,
                 home_settings: HomeSettings) -> None:
        self.logging_level = logging_level
        self.language = language
        self.measurement_system = measurement_system
        self.concurrency_priority = concurrency_priority
        self.integration_settings = integration_settings
        self.home_settings = home_settings
