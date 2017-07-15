import datetime
import configparser
import discord
from weather import WeatherService

class CommandHandler(object):
    def __init__(self, discord_client: discord.Client, weather_service: WeatherService):
        self.discord_client = discord_client
        self.weather_service = weather_service

    async def handle(self, command):
        if not command.content.startswith("!meteo") and not command.content.startswith("!weather"):
            return

        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        weather = self.weather_service.get_forecast("Nantes,fr", tomorrow)
        embed = self.__create_embed_weather__(weather, "Nantes", tomorrow)

        await self.discord_client.send_message(command.channel, embed=embed)

    @staticmethod
    def __weather_code_to_google_icon_url__(weather_code: int) -> str:
        TEMPLATE = "https://ssl.gstatic.com/onebox/weather/{}/{}.png"
        SIZE = "64"

        config = configparser.ConfigParser()
        config.read("config/google_icons.ini")

        google_icon_code = config["GoogleIcons"][str(weather_code)]

        return TEMPLATE.format(SIZE, google_icon_code)

    def __create_embed_weather__(self, weather, place, date) -> discord.Embed:
        detailed_status = weather._detailed_status.title()
        weather_code = weather._weather_code
        humidity = weather.get_humidity()
        temperature_min = weather.get_temperature("celsius")["min"]
        temperature_max = weather.get_temperature("celsius")["max"]
        wind_speed = int(weather.get_wind()["speed"] * 3.6)
        icon_url = CommandHandler.__weather_code_to_google_icon_url__(weather_code)

        embed = discord.Embed(colour=0x00FF00)
        embed.title = "Weather forecast @ {}: tomorrow ({})".format(place, date.strftime("%A %d %B"))
        embed.description = detailed_status
        embed.add_field(name="High temp.", value=str(int(temperature_max)) + "°C")
        embed.add_field(name="Low temp.", value=str(int(temperature_min)) + "°C")
        embed.add_field(name="Humidity", value=str(humidity) + "%")
        embed.add_field(name="Wind", value=str(wind_speed) + " km/h")
        embed.set_thumbnail(url=icon_url)
        embed.set_footer(text="github.com/mbouchenoire/discloud", icon_url="https://avatars6.githubusercontent.com/u/8810050?v=4&s=460")

        return embed

    
