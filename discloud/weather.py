import pyowm

class WeatherService(object):
    def __init__(self, pyowm_api_key: str):
        self.owm = pyowm.OWM(pyowm_api_key)

    def get_forecast(self, place: str, when):
        forecast = self.owm.daily_forecast(place)
        return forecast.get_weather_at(when)
    