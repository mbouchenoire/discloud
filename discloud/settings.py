class IntegrationSettings(object):
    def __init__(self, discord_bot_token: str, open_weather_map_api_key: str) -> None:
        self.discord_bot_token = discord_bot_token
        self.open_weather_map_api_key = open_weather_map_api_key


class HomeSettings(object):
    def __init__(self, full_name: str, display_name: str, update_frequency: int) -> None:
        self.full_name = full_name
        self.display_name = display_name
        self.update_frequency = int(update_frequency)


class TemperatureSettings(object):
    def __init__(self, unit: str, threshold_hot: int, threshold_cold: int, threshold_color: str) -> None:
        self.unit = unit
        self.threshold_hot = int(threshold_hot)
        self.threshold_cold = int(threshold_cold)
        self.threshold_color = threshold_color


class ApplicationSettings(object):
    def __init__(self,
                 integration_settings: IntegrationSettings,
                 home_settings: HomeSettings,
                 temperature_settings: TemperatureSettings) -> None:
        self.integration_settings = integration_settings
        self.home_settings = home_settings
        self.temperature_settings = temperature_settings
