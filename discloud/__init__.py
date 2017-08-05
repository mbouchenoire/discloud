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

import os
import sys
import logging
from typing import List
from settings import MeasurementSystem, Language, ConcurrencyPriority, IntegrationSettings, HomeSettings, ApplicationSettings
from main import Application


class ConfigurationFactory(object):
    _LOGGING_LEVELS = {"critical": logging.DEBUG,
                       "fatal": logging.FATAL,
                       "error": logging.INFO,
                       "warning": logging.WARNING,
                       "warn": logging.WARN,
                       "info": logging.ERROR,
                       "debug": logging.DEBUG}

    _LANGUAGES = {"en": Language.ENGLISH,
                  "ru": Language.RUSSIAN,
                  "jp": Language.JAPANESE,
                  "de": Language.GERMAN,
                  "es": Language.SPANISH,
                  "fr": Language.FRENCH}

    _MEASUREMENT_SYSTEMS = {"metric": MeasurementSystem.METRIC,
                            "imperial": MeasurementSystem.IMPERIAL}

    _CONCURRENCY_PRIORITIES = {"always": ConcurrencyPriority.ALWAYS,
                               "auto": ConcurrencyPriority.AUTO,
                               "never": ConcurrencyPriority.NEVER}

    _DEFAULT_LOGGING_LEVEL = "info"
    _DEFAULT_LANGUAGE = "en"
    _DEFAULT_MEASUREMENT_SYSTEM = "metric"
    _DEFAULT_CONCURRENCY_PRIORITY = "auto"
    _DEFAULT_CHANNELS = "general,weather"
    _DEFAULT_MORNING_FORECAST_TIME = "8:00"
    _DEFAULT_EVENING_FORECAST_TIME = "20:00"

    def __init__(self):
        self.is_configuration_valid = True

    @staticmethod
    def __parse_array__(array_str: str) -> List[str]:
        return array_str.split(",")

    def __abort_start__(self, message: str) -> None:
        self.is_configuration_valid = False
        logging.error(message)
        return None

    def __parse_dict__(self, key: str, value: str, reference_dict: dict):
        if value not in reference_dict:
            valid_values = ",".join(reference_dict.keys())
            msg_template = "invalid value '{}' for environment variable '{}', valid values are: {}"
            return self.__abort_start__(msg_template.format(value, key, valid_values))

        return reference_dict[value.lower()]

    def __read_env_variable__(self, key: str, default_value: str) -> str:
        try:
            return os.environ[key]
        except KeyError:
            if default_value:
                msg_template = "optional environment variable '{}' is not defined, default value '{}' will be used"
                logging.info(msg_template.format(key, default_value))
                return default_value
            else:
                msg = "required environment variable '{}' is not defined, the bot will NOT start".format(key)
                return self.__abort_start__(msg)

    def create(self) -> ApplicationSettings:
        logging_level_str = self.__read_env_variable__("LOGGING_LEVEL",
                                                       ConfigurationFactory._DEFAULT_LOGGING_LEVEL)

        logging_level = self.__parse_dict__("LOGGING_LEVEL",
                                            logging_level_str,
                                            ConfigurationFactory._LOGGING_LEVELS)

        language_str = self.__read_env_variable__("LANGUAGE", ConfigurationFactory._DEFAULT_LANGUAGE)
        language = self.__parse_dict__("LANGUAGE", language_str, ConfigurationFactory._LANGUAGES)

        measurement_system_str = self.__read_env_variable__("MEASUREMENT_SYSTEM",
                                                            ConfigurationFactory._DEFAULT_MEASUREMENT_SYSTEM)

        measurement_system = self.__parse_dict__("MEASUREMENT_SYSTEM",
                                                 measurement_system_str,
                                                 ConfigurationFactory._MEASUREMENT_SYSTEMS)

        concurrency_priority_str = self.__read_env_variable__("CONCURRENCY_PRIORITY",
                                                              ConfigurationFactory._DEFAULT_CONCURRENCY_PRIORITY)

        concurrency_priority = self.__parse_dict__("CONCURRENCY_PRIORITY",
                                                   concurrency_priority_str,
                                                   ConfigurationFactory._CONCURRENCY_PRIORITIES)

        discord_bot_token = self.__read_env_variable__("DISCORD_BOT_TOKEN", None)
        open_weather_map_api_key = self.__read_env_variable__("OPEN_WEATHER_MAP_API_KEY", None)
        weather_underground_api_key = self.__read_env_variable__("WEATHER_UNDERGROUND_API_KEY", "")
        home_full_name = self.__read_env_variable__("HOME_FULL_NAME", None)
        home_display_name = self.__read_env_variable__("HOME_DISPLAY_NAME", home_full_name)

        periodic_forecast_channels_str = self.__read_env_variable__("PERIODIC_FORECAST_CHANNELS",
                                                                    ConfigurationFactory._DEFAULT_CHANNELS)

        periodic_forecast_channels = ConfigurationFactory.__parse_array__(periodic_forecast_channels_str)

        morning_forecast_time = self.__read_env_variable__("MORNING_FORECAST_TIME",
                                                           ConfigurationFactory._DEFAULT_MORNING_FORECAST_TIME)

        evening_forecast_time = self.__read_env_variable__("EVENING_FORECAST_TIME",
                                                           ConfigurationFactory._DEFAULT_EVENING_FORECAST_TIME)

        integration_settings = IntegrationSettings(discord_bot_token,
                                                   open_weather_map_api_key,
                                                   weather_underground_api_key)

        home_settings = HomeSettings(home_full_name,
                                     home_display_name,
                                     periodic_forecast_channels,
                                     morning_forecast_time,
                                     evening_forecast_time)

        application_settings = ApplicationSettings(logging_level,
                                                   language,
                                                   measurement_system,
                                                   concurrency_priority,
                                                   integration_settings,
                                                   home_settings)

        return application_settings

logging.basicConfig(level=logging.INFO)

configuration_factory = ConfigurationFactory()
configuration = configuration_factory.create()

if not configuration_factory.is_configuration_valid:
    logging.error("the bot configuration is invalid, the application will NOT start")
    sys.exit(1)

logging.basicConfig(level=configuration.logging_level)

Application(configuration).run()
