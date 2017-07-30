from enum import Enum
from typing import List


class MeasurementSystem(Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"


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
        self.morning_forecast_time = morning_forecast_time
        self.evening_forecast_time = evening_forecast_time


class ApplicationSettings(object):
    def __init__(self,
                 measurement_system: MeasurementSystem,
                 integration_settings: IntegrationSettings,
                 home_settings: HomeSettings) -> None:
        self.measurement_system = measurement_system
        self.integration_settings = integration_settings
        self.home_settings = home_settings
