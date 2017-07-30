import discord
from command import CommandHandler, WeatherDiscordService
from weather import WeatherServiceLocator
from settings import ApplicationSettings


class Application(object):
    def __init__(self, application_settings: ApplicationSettings) -> None:
        self._settings = application_settings

    def run(self) -> None:
        discord_client = discord.Client()

        weather_service_locator = WeatherServiceLocator(self._settings.integration_settings.open_weather_map_api_key)
        command_handler = CommandHandler(self._settings.measurement_system,
                                         self._settings.home_settings,
                                         weather_service_locator,
                                         discord_client)
        weather_discord_service = WeatherDiscordService(self._settings.measurement_system,
                                                        self._settings.home_settings,
                                                        weather_service_locator,
                                                        discord_client)

        @discord_client.event
        async def on_message(message) -> None:
            await command_handler.handle(message)

        discord_client.loop.create_task(weather_discord_service.send_home_forecast())
        discord_client.loop.create_task(weather_discord_service.update_profile())
        discord_client.loop.create_task(weather_discord_service.update_presence())
        discord_client.run(self._settings.integration_settings.discord_bot_token)
