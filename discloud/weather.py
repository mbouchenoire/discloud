import datetime
import pyowm
from typing import List
from settings import MeasurementSystem


class Weather(object):
    def __init__(self, location: str, date: datetime.date, measurement_system: MeasurementSystem,
                 weather_code: int, temperature: float, humidity: int, wind_speed: int) -> None:
        self.location = location
        self.date = date
        self.measurement_system = measurement_system
        self.weather_code = weather_code
        self.temperature = temperature
        self.humidity = humidity
        self.wind_speed = wind_speed


class WeatherForecast(object):
    def __init__(self, weathers: List[Weather]) -> None:
        self.weathers = weathers


class WeatherService(object):
    def get_weather(self, location: str, measurement_system: MeasurementSystem) -> Weather:
        pass

    def get_forecast(self, location: str, measurement_system: MeasurementSystem) -> WeatherForecast:
        pass


class OwmWeatherService(WeatherService):
    def __init__(self, pyowm_api_key: str) -> None:
        self._owm = pyowm.OWM(pyowm_api_key)

    @staticmethod
    def __get_temperature_unit__(measurement_system: MeasurementSystem):
        if measurement_system is MeasurementSystem.METRIC:
            return "celsius"
        elif measurement_system is MeasurementSystem.IMPERIAL:
            return "kelvin"
        else:
            raise ValueError("measurement system must be either metric or imperial")

    @staticmethod
    def __get_wind_unit(measurement_system: MeasurementSystem):
        if measurement_system is MeasurementSystem.METRIC:
            return "meters_sec"
        elif measurement_system is MeasurementSystem.IMPERIAL:
            return "miles_hour"
        else:
            raise ValueError("measurement system must be either metric or imperial")

    @staticmethod
    def __build_weather__(location: str, owm_weather, measurement_system: MeasurementSystem) -> Weather:
        temperature_unit = OwmWeatherService.__get_temperature_unit__(measurement_system)
        wind_unit = OwmWeatherService.__get_wind_unit(measurement_system)

        weather_code = owm_weather.get_weather_code()
        humidity = owm_weather.get_humidity()

        owm_temperature = owm_weather.get_temperature(temperature_unit)

        if "temp" in owm_temperature:
            temperature = owm_temperature["temp"]
        elif "day" in owm_temperature:
            temperature = owm_temperature["day"]
        else:
            raise ValueError("the temperature cannot be extracted from owm temperature object")

        wind_speed = int(owm_weather.get_wind(wind_unit)["speed"])

        if measurement_system is MeasurementSystem.METRIC:
            wind_speed = wind_speed * 3.6  # m/s to km/h

        weather = Weather(location, datetime.date.today(), measurement_system,
                          weather_code, temperature, humidity, wind_speed)

        return weather

    def get_weather(self, location: str, measurement_system: MeasurementSystem) -> Weather:
        owm_weather = self._owm.weather_at_place(location).get_weather()
        return OwmWeatherService.__build_weather__(location, owm_weather, measurement_system)

    def get_forecast(self, location: str, measurement_system: MeasurementSystem) -> WeatherForecast:
        forecast = self._owm.daily_forecast(location)
        weathers = [OwmWeatherService.__build_weather__(location, weather, measurement_system)
                    for weather in forecast.get_forecast()]
        return WeatherForecast(weathers)


class WeatherServiceLocator(object):
    def __init__(self, owm_api_key: str) -> None:
        self._owm = OwmWeatherService(owm_api_key)

    def get_weather_service(self) -> WeatherService:
        return self._owm
