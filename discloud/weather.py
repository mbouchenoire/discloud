import datetime
import pyowm

class WeatherService(object):
    def __init__(self, pyowm_api_key: str):
        self.owm = pyowm.OWM(pyowm_api_key)

    def get_forecast(self, place: str, when: datetime.datetime):
        is_today = when.date() == datetime.date.today()

        if is_today:
            return self.owm.weather_at_place(place).get_weather()
        else:
            forecast = self.owm.daily_forecast(place)
            return forecast.get_weather_at(when)
    