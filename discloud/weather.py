import datetime
import configparser
import logging
import pyowm
import discord

class WeatherService(object):
    def __init__(self, pyowm_api_key: str, discord_client: discord.Client):
        self.owm = pyowm.OWM(pyowm_api_key)
        self.discord_client = discord_client

    @staticmethod
    def __get_avatar_bytes__(weather_code):
        config = configparser.ConfigParser()
        config.read("config/open_weather_map.ini")

        google_icon_code = config["Icons"][str(weather_code)]

        f = open("images/google/{}.png".format(google_icon_code), "rb")
        
        try:
            avatar_bytes = f.read()
        finally:
            f.close()

        return avatar_bytes

    def get_forecast(self, place: str, when: datetime.datetime):
        is_today = when.date() == datetime.date.today()

        if is_today:
            return self.owm.weather_at_place(place).get_weather()
        else:
            forecast = self.owm.daily_forecast(place)
            return forecast.get_weather_at(when)

    async def update_realtime_weather(self, place: str):
        weather = self.owm.weather_at_place(place).get_weather()
        avatar_bytes = WeatherService.__get_avatar_bytes__(weather._weather_code)

        temp = weather.get_temperature("celsius")["temp"]
        status_text = "{}°C @ {}".format(str(int(temp)), place)

        logging.info("updating discloud profile presence...")
        await self.discord_client.change_presence(game=discord.Game(name=status_text))
        
        logging.info("updating discloud profile avatar...")
        await self.discord_client.edit_profile(password=None, avatar=avatar_bytes)
