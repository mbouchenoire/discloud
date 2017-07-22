import datetime
import pyowm


class OwmWeatherService(object):
    def __init__(self, pyowm_api_key: str) -> None:
        self._owm = pyowm.OWM(pyowm_api_key)

    def get_weather(self, place: str, when=datetime.datetime.now()):
        is_today = when.date() == datetime.date.today()

        if is_today:
            return self._owm.weather_at_place(place).get_weather()
        else:
            forecast = self._owm.daily_forecast(place)
            return forecast.get_weather_at(when)
