import datetime
import configparser
import discord
from weather import WeatherService

class CommandHandler(object):
    def __init__(self, discord_client: discord.Client, weather_service: WeatherService):
        self.discord_client = discord_client
        self.weather_service = weather_service

    async def handle(self, command):
        INVALID_FORMAT_MESSAGE = "the weather command format must be '!weather <offset>@<place>' (e.g. !weather +1@Nantes)"

        content = command.content

        if not content.startswith("!meteo") and not content.startswith("!weather"):
            return

        content = content.replace("!meteo", "").replace("!weather", "")

        if "@" not in content:
            return await self.discord_client.send_message(command.channel, INVALID_FORMAT_MESSAGE)

        parts = content.split("@")

        if len(parts) != 2:
            return await self.discord_client.send_message(command.channel, INVALID_FORMAT_MESSAGE)

        offset_str = parts[0]
        place = parts[1]

        offset = 0

        if offset_str is not None and offset_str.strip() != "":
            offset = int(offset_str)

            if offset < 0:
                return await self.discord_client.send_message(command.channel, "the forecast daily offset must be >= 0")

        if place is None or place == "":
            return await self.discord_client.send_message(command.channel, "the place is mandatory (@<place>)")

        day = datetime.datetime.today() + datetime.timedelta(days=offset)
        weather = self.weather_service.get_forecast(place, day)
        embed = self.__create_embed_weather__(weather, day, place)

        await self.discord_client.send_message(command.channel, embed=embed)

    @staticmethod
    def __weather_code_to_google_icon_url__(weather_code: int) -> str:
        TEMPLATE = "https://ssl.gstatic.com/onebox/weather/{}/{}.png"
        SIZE = "64"

        config = configparser.ConfigParser()
        config.read("config/open_weather_map.ini")

        google_icon_code = config["Icons"][str(weather_code)]

        return TEMPLATE.format(SIZE, google_icon_code)

    @staticmethod
    def __get_color__(weather_code: int, temperature_min: float, temperature_max: float) -> int:
        COLORS = {"green": 0x4CAF50, "light_green": 0x8BC34A, "lime": 0xCDDC39, 
                    "yellow": 0xFFEB3B, "amber": 0xFFC107, "orange": 0xFF9800, "deep_orange": 0xFF5722, "red": 0xF44336}

        config = configparser.ConfigParser()
        
        config.read("config/temperature.ini")
        cold_threshold = int(config["Thresholds"]["cold"])
        hot_threshold = int(config["Thresholds"]["hot"])
        temperature_threshold_color = config["Thresholds"]["color"]

        if temperature_min <= cold_threshold or temperature_max >= hot_threshold:
            return COLORS[temperature_threshold_color]

        config.read("config/open_weather_map.ini")
        weather_color_code = config["Colors"][str(weather_code)]

        return COLORS[weather_color_code]

    def __create_embed_weather__(self, weather, date, place) -> discord.Embed:
        detailed_status = weather._detailed_status.title()
        weather_code = weather._weather_code
        humidity = weather.get_humidity()
        temperature = weather.get_temperature("celsius")

        temperature_min = None
        temperature_max = None
        
        if "temp_min" in temperature: # when manipulating today's weather (observation)
            temperature_min = temperature["temp_min"]
            temperature_max = temperature["temp_max"]
        elif "min" in temperature: # when manipulating forecast
            temperature_min = temperature["min"]
            temperature_max = temperature["max"]

        wind_speed = int(weather.get_wind()["speed"] * 3.6)
        icon_url = CommandHandler.__weather_code_to_google_icon_url__(weather_code)

        color = CommandHandler.__get_color__(weather_code, temperature_min, temperature_max)
        embed = discord.Embed(colour=color)
        embed.title = "{} @ {}".format(date.strftime("%A %d %B"), place.title())
        embed.description = detailed_status
        embed.add_field(name="High temp.", value=str(int(temperature_max)) + "°C")
        embed.add_field(name="Low temp.", value=str(int(temperature_min)) + "°C")
        embed.add_field(name="Humidity", value=str(humidity) + "%")
        embed.add_field(name="Wind", value=str(wind_speed) + " km/h")
        embed.set_thumbnail(url=icon_url)
        embed.set_footer(text="github.com/mbouchenoire/discloud", icon_url="https://avatars6.githubusercontent.com/u/8810050?v=4&s=460")

        return embed

    