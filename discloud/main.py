import asyncio
import discord
from command_handler import CommandHandler
from weather import WeatherService
from settings import IntegrationSettings, HomeSettings, TemperatureSettings, ApplicationSettings


class Application(object):
    def __init__(self, application_settings: ApplicationSettings) -> None:
        self.settings = application_settings

    def run(self) -> None:
        discord_client = discord.Client()
        weather_service = WeatherService(self.settings.integration_settings.open_weather_map_api_key, discord_client)

        @discord_client.event
        async def on_message(message) -> None:
            await CommandHandler(discord_client, weather_service, self.settings.temperature_settings).handle(message)

        async def update_realtime_weather() -> None:
            await discord_client.wait_until_ready()

            while not discord_client.is_closed:
                await weather_service.update_realtime_weather(self.settings.home_settings,
                                                              self.settings.temperature_settings.unit)

                await asyncio.sleep(self.settings.home_settings.update_frequency * 60)

        discord_client.loop.create_task(update_realtime_weather())
        discord_client.run(self.settings.integration_settings.discord_bot_token)






