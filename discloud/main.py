import asyncio
import datetime
import discord
from command_handler import CommandHandler
from weather import WeatherService

class Main(object):
    def __init__(self, discord_bot_token: str, discord_channel_id: str, open_weather_map_api_key: str, home: str, update_frequency: int):
        self.discord_bot_token = discord_bot_token
        self.discord_channel_id = discord_channel_id
        self.open_weather_map_api_key = open_weather_map_api_key
        self.home = home
        self.update_frequency = update_frequency

    def run(self):
        discord_client = discord.Client()
        weather_service = WeatherService(self.open_weather_map_api_key, discord_client)

        @discord_client.event
        async def on_message(message):
            await CommandHandler(discord_client, weather_service).handle(message)

        async def update_realtime_weather():
            await discord_client.wait_until_ready()

            while not discord_client.is_closed:
                await weather_service.update_realtime_weather(self.home)
                await asyncio.sleep(self.update_frequency)

        discord_client.loop.create_task(update_realtime_weather())
        discord_client.run(self.discord_bot_token)
