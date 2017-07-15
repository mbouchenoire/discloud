import discord
from command_handler import CommandHandler
from weather import WeatherService

class Main(object):
    def __init__(self, discord_bot_token: str, discord_channel_id: str, open_weather_map_api_key: str):
        self.discord_bot_token = discord_bot_token
        self.discord_channel_id = discord_channel_id
        self.open_weather_map_api_key = open_weather_map_api_key

    def run(self):
        discord_client = discord.Client()
        weather_service = WeatherService(self.open_weather_map_api_key)

        @discord_client.event
        async def on_message(message):
            await CommandHandler(discord_client, weather_service).handle(message)

        discord_client.run(self.discord_bot_token)
