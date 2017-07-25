import asyncio
import logging
import discord
from command_handler import CommandHandler
from weather import OwmWeatherService
from realtime_weather import RealTimeWeatherService
from settings import ApplicationSettings


class Application(object):
    def __init__(self, application_settings: ApplicationSettings) -> None:
        self._settings = application_settings

    def run(self) -> None:
        discord_client = discord.Client()

        owm_weather_service = OwmWeatherService(self._settings.integration_settings.open_weather_map_api_key)

        command_handler = CommandHandler(owm_weather_service, self._settings.temperature_settings, discord_client)

        realtime_weather_service = RealTimeWeatherService(owm_weather_service,
                                                          self._settings.home_settings,
                                                          self._settings.temperature_settings,
                                                          discord_client)

        @discord_client.event
        async def on_message(message) -> None:
            await command_handler.handle(message)

        async def update_realtime_weather() -> None:
            await discord_client.wait_until_ready()
            logging.info("discord client is now ready")

            while not discord_client.is_closed:
                try:
                    logging.info("updating realtime weather...")
                    await realtime_weather_service.update_realtime_weather()
                    logging.info("realtime weather updated successfully")
                except:
                    logging.exception("failed to update realtime weather")

                await asyncio.sleep(self._settings.home_settings.update_frequency * 60)

            logging.warning("discord client has disconnected")

        discord_client.loop.create_task(update_realtime_weather())
        discord_client.run(self._settings.integration_settings.discord_bot_token)
