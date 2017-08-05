# Copyright (C) 2017 discloud
#
# This file is part of discloud.
#
# discloud is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# discloud is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with discloud.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
import configparser
import json
import http.client
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


class WeatherRepository(object):
    def is_queryable(self) -> bool:
        pass

    def get_weather(self, location: str, measurement_system: MeasurementSystem) -> Weather:
        pass

    def get_forecast(self, location: str, measurement_system: MeasurementSystem) -> WeatherForecast:
        pass


class WeatherUndergroundRepository(WeatherRepository):
    NAME = "WU"

    _HOST = "api.wunderground.com"
    _REQUESTS_PER_MINUTE = 9 # should be 10 but we keep it safe

    def __init__(self, wu_api_key: str) -> None:
        self._wu_api_key = wu_api_key
        self._past_requests = list()

    @staticmethod
    def __get_json__(endpoint: str, title: str):
        conn = http.client.HTTPSConnection(WeatherUndergroundRepository._HOST)

        try:
            conn.request("GET", endpoint)
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            return json.loads(data)
        except:
            logging.exception("failed to fetch the " + title + " from Weather Underground")
            return None
        finally:
            conn.close()

    @staticmethod
    def __get_weather_code__(wu_icon_code: str) -> int:
        config = configparser.ConfigParser()
        config.read("config/weather_underground.ini")
        return config["owm-codes"][wu_icon_code]

    def __get_weather_json__(self, location: str):
        endpoint_template = "/api/{}/conditions/q/{}.json"
        return WeatherUndergroundRepository.__get_json__(endpoint_template.format(self._wu_api_key, location),
                                                         "weather")

    def __get_forecast_json__(self, location: str):
        endpoint_template = "/api/{}/forecast/q/{}.json"
        return WeatherUndergroundRepository.__get_json__(endpoint_template.format(self._wu_api_key, location),
                                                         "weather forecast")

    def is_queryable(self) -> bool:
        if len(self._past_requests) > WeatherUndergroundRepository._REQUESTS_PER_MINUTE:
            raise ValueError("there are too many requests in the queue")

        if len(self._past_requests) < WeatherUndergroundRepository._REQUESTS_PER_MINUTE:
            return True

        oldest_request = self._past_requests[-1]
        seconds_since_oldest_request = (datetime.datetime.now() - oldest_request).total_seconds()

        return seconds_since_oldest_request <= 60

    def get_weather(self, location: str, measurement_system: MeasurementSystem) -> Weather:
        logging.debug("retrieving current weather @{} using Weather Underground...".format(location))

        weather_json = self.__get_weather_json__(location)
        current_observation = weather_json["current_observation"]

        date = datetime.date.today()
        wu_icon = current_observation["icon"]
        weather_code = WeatherUndergroundRepository.__get_weather_code__(wu_icon)

        if measurement_system is MeasurementSystem.METRIC:
            temperature_str = current_observation["temp_c"]
            wind_speed_str = current_observation["wind_kph"]
        else:
            temperature_str = current_observation["temp_f"]
            wind_speed_str = current_observation["wind_mph"]

        temperature = float(temperature_str)
        humidity_str = current_observation["relative_humidity"].replace("%", "")
        humidity = int(humidity_str)
        wind_speed = int(wind_speed_str)

        self._past_requests.insert(0, datetime.datetime.now())

        if len(self._past_requests) > WeatherUndergroundRepository._REQUESTS_PER_MINUTE:
            self._past_requests.pop()

        return Weather(location, date, measurement_system, weather_code, temperature, humidity, wind_speed)

    def get_forecast(self, location: str, measurement_system: MeasurementSystem) -> WeatherForecast:
        logging.debug("retrieving weather forecast @{} using Weather Underground...".format(location))

        forecast_json = self.__get_forecast_json__(location)
        weathers = list()

        forec = forecast_json["forecast"]
        simplef = forec["simpleforecast"]
        tday = simplef["forecastday"]

        for json_weather in tday:
            epoch_str = json_weather["date"]["epoch"]
            date = datetime.date.fromtimestamp(int(epoch_str))
            weather_code = WeatherUndergroundRepository.__get_weather_code__(json_weather["icon"])

            if measurement_system is MeasurementSystem.METRIC:
                temperature_str = json_weather["high"]["celsius"]
                wind_speed_str = json_weather["avewind"]["kph"]
            else:
                temperature_str = json_weather["high"]["fahrenheit"]
                wind_speed_str = json_weather["avewind"]["mph"]

            temperature = float(temperature_str)
            humidity = json_weather["avehumidity"]
            wind_speed = int(wind_speed_str)

            weather = Weather(location, date, measurement_system, weather_code, temperature, humidity, wind_speed)

            weathers.append(weather)

        self._past_requests.insert(0, datetime.datetime.now())

        if len(self._past_requests) > WeatherUndergroundRepository._REQUESTS_PER_MINUTE:
            self._past_requests.pop()

        return WeatherForecast(weathers)


class OpenWeatherMapRepository(WeatherRepository):
    NAME = "OWM"

    def __init__(self, owm_api_key: str) -> None:
        self._owm = pyowm.OWM(owm_api_key)

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
        temperature_unit = OpenWeatherMapRepository.__get_temperature_unit__(measurement_system)
        wind_unit = OpenWeatherMapRepository.__get_wind_unit(measurement_system)

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

        date = datetime.date.fromtimestamp(owm_weather.get_reference_time())

        weather = Weather(location, date, measurement_system,
                          weather_code, temperature, humidity, wind_speed)

        return weather

    def is_queryable(self) -> bool:
        return True

    def get_weather(self, location: str, measurement_system: MeasurementSystem) -> Weather:
        logging.debug("retrieving current weather @{} using Open Weather Map...".format(location))
        owm_weather = self._owm.weather_at_place(location).get_weather()
        return OpenWeatherMapRepository.__build_weather__(location, owm_weather, measurement_system)

    def get_forecast(self, location: str, measurement_system: MeasurementSystem) -> WeatherForecast:
        logging.debug("retrieving weather forecast @{} using Open Weather Map...".format(location))
        forecast = self._owm.daily_forecast(location)

        weathers = [OpenWeatherMapRepository.__build_weather__(location, weather, measurement_system)
                    for weather in forecast.get_forecast()]

        return WeatherForecast(weathers)


class WeatherService(object):
    def __init__(self, owm_api_key: str, wu_api_key: str) -> None:
        if not owm_api_key and not wu_api_key:
            raise ValueError("at least one weather api key (Open Weather Map or Weather Underground) must be provided")

        self._owm = OpenWeatherMapRepository(owm_api_key) if owm_api_key else None
        self._wu = WeatherUndergroundRepository(wu_api_key) if wu_api_key else None

    def __get_weather_repository__(self):
        if self._wu is not None and self._wu.is_queryable():
            return self._wu
        elif self._owm is not None and self._owm.is_queryable():
            return self._owm
        else:
            raise ValueError("there is no queryable weather repository at the moment")

    def get_weather(self, location: str, measurement_system: MeasurementSystem) -> Weather:
        return self.__get_weather_repository__().get_weather(location, measurement_system)

    def get_forecast(self, location: str, measurement_system: MeasurementSystem) -> WeatherForecast:
        return self.__get_weather_repository__().get_forecast(location, measurement_system)
