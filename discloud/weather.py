import datetime
import logging
import pyowm


class OwmWeatherService(object):
    def __init__(self, pyowm_api_key: str) -> None:
        self._owm = pyowm.OWM(pyowm_api_key)

    def get_weather(self, place: str, when=datetime.datetime.now()):
        is_today = when.date() == datetime.date.today()

        logging.debug("retrieving weather: " + str(when) + "@" + place + "...")

        if is_today:
            weather = self._owm.weather_at_place(place).get_weather()
        else:
            forecast = self._owm.daily_forecast(place)
            weather = forecast.get_weather_at(when)

        logging.debug("weather has been retrieved successfully")

        return weather
