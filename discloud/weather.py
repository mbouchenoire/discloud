import datetime
import logging
import pyowm


class OwmWeatherService(object):
    def __init__(self, pyowm_api_key: str) -> None:
        self._owm = pyowm.OWM(pyowm_api_key)

    def get_weather(self, place: str):
        logging.debug("retrieving weather: now@" + place + "...")

        weather = self._owm.weather_at_place(place).get_weather()

        logging.debug("weather has been retrieved successfully")

        return weather

    def get_forecast(self, place: str, when: datetime.date):
        logging.debug("retrieving weather forecast: " + str(when) + "@" + place + "...")

        forecast = self._owm.daily_forecast(place)
        weather = forecast.get_weather_at(when)

        logging.debug("weather forecast has been retrieved successfully")

        return weather
