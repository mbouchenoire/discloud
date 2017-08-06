import configparser
from settings import Language, MeasurementSystem, ApplicationSettings
from weather import Weather, WeatherForecast


class MessageFactory(object):
    _OWM_CONFIG_PATH = "config/open_weather_map.ini"

    _DIGITS_WIDTHS = {'0': 3, '1': 2, '2': 3, '3': 3, '4': 3, '5': 3, '6': 3, '7': 3, '8': 3, '9': 3}

    _LOWERS_WIDTHS = {'a': 3, 'b': 3, 'c': 3, 'd': 3, 'e': 3, 'f': 2, 'g': 3, 'h': 3, 'i': 2, 'j': 2, 'k': 3, 'l': 2,
                      'm': 4.5, 'n': 3, 'o': 3, 'p': 3, 'q': 3, 'r': 2.75, 's': 2.75, 't': 2.75, 'u': 3, 'v': 3,
                      'w': 4.5, 'x': 3, 'y': 3, 'z': 3}

    _UPPERS_WIDTHS = {'A': 5, 'B': 4, 'C': 5, 'D': 5, 'E': 4, 'F': 4, 'G': 5, 'H': 5, 'I': 3, 'J': 3, 'K': 5, 'L': 4,
                      'M': 6, 'N': 5, 'O': 5.5, 'P': 4, 'Q': 5.5, 'R': 4, 'S': 4, 'T': 5, 'U': 5, 'V': 5,
                      'W': 6.5, 'X': 5, 'Y': 5, 'Z': 5}

    _SPECIALS_WIDTHS = {' ': 1, '.': 1, '°': 1, '%': 1}

    _CHARACTERS_WIDTHS = {**_DIGITS_WIDTHS, **_LOWERS_WIDTHS, **_UPPERS_WIDTHS, **_SPECIALS_WIDTHS}

    def __init__(self, application_settings: ApplicationSettings):
        self._application_settings = application_settings

    @staticmethod
    def __get_text_width__(text: str) -> float:
        width = 0

        for c in text:
            if c in MessageFactory._CHARACTERS_WIDTHS:
                width += MessageFactory._CHARACTERS_WIDTHS[c]
            else:
                width += 1

        return width

    @staticmethod
    def __get_temperature_suffix__(measurement_system: MeasurementSystem) -> str:
        if measurement_system is MeasurementSystem.METRIC:
            return "°C"
        elif measurement_system is MeasurementSystem.IMPERIAL:
            return "°F"
        else:
            raise ValueError("measurement system must be either metric or imperial")

    @staticmethod
    def __get_wind_speed_suffix__(measurement_system: MeasurementSystem) -> str:
        if measurement_system is MeasurementSystem.METRIC:
            return " kmh"
        elif measurement_system is MeasurementSystem.IMPERIAL:
            return " mph"

    @staticmethod
    def __add_margin__(text: str, max_width: float) -> str:
        text_width = MessageFactory.__get_text_width__(text)
        full_date_margin = round(max_width) - round(text_width)
        return (" " * full_date_margin) + text

    def __get_localized_weekday__(self, weekday_index: int) -> str:
        config = configparser.ConfigParser()
        config.read("i18n/{}.ini".format(self._application_settings.language.value))
        return config["weekdays"][str(weekday_index)]

    def format_weather_forecast(self, forecast: WeatherForecast) -> str:
        config = configparser.ConfigParser()
        config.read(MessageFactory._OWM_CONFIG_PATH)

        msg = "**@ " + forecast.weathers[0].location.title() + "**\n\n"

        for weather in forecast.weathers:
            weekday_index = weather.date.weekday()
            week_day = self.__get_localized_weekday__(weekday_index)
            full_date = week_day
            full_date = MessageFactory.__add_margin__(full_date, 10.5)

            discord_icon_code = config["discord-icons"][str(weather.weather_code)]
            temperature_suffix = MessageFactory.__get_temperature_suffix__(weather.measurement_system)
            humidity_suffix = "%"
            wind_speed_suffix = MessageFactory.__get_wind_speed_suffix__(weather.measurement_system)

            str_temperature = str(round(weather.temperature))
            str_humidity = str(weather.humidity)
            str_wind_speed = str(round(weather.wind_speed))

            full_temperature = str_temperature + temperature_suffix
            full_humidity = str_humidity + humidity_suffix
            full_wind_speed = str_wind_speed + wind_speed_suffix

            full_temperature = MessageFactory.__add_margin__(full_temperature,
                                                             MessageFactory.__get_text_width__("999"
                                                                                               + temperature_suffix))
            full_humidity = MessageFactory.__add_margin__(full_humidity,
                                                          MessageFactory.__get_text_width__("100%"))

            full_wind_speed = MessageFactory.__add_margin__(full_wind_speed,
                                                            MessageFactory.__get_text_width__("999"
                                                                                              + wind_speed_suffix))

            msg += "{}   :{}:   {}   {}   {}\n".format(full_date,
                                                       discord_icon_code,
                                                       full_temperature,
                                                       full_humidity,
                                                       full_wind_speed)

        return msg

    def format_weather(self, weather: Weather) -> str:
        config = configparser.ConfigParser()
        config.read(MessageFactory._OWM_CONFIG_PATH)

        is_home = self._application_settings.home_settings.display_name.upper() == weather.location.upper()

        header = "" if is_home else "**@ " + weather.location.title() + "**: "
        discord_icon_code = config["discord-icons"][str(weather.weather_code)]
        temperature_suffix = MessageFactory.__get_temperature_suffix__(weather.measurement_system)
        wind_speed_suffix = MessageFactory.__get_wind_speed_suffix__(weather.measurement_system)

        return "{}:{}:   {}{}   {}%   {}{}".format(header,
                                                   discord_icon_code,
                                                   round(weather.temperature), temperature_suffix,
                                                   weather.humidity,
                                                   round(weather.wind_speed), wind_speed_suffix)

    @staticmethod
    def format_presence(weather: Weather, should_help: bool) -> str:
        temperature_suffix = MessageFactory.__get_temperature_suffix__(weather.measurement_system)
        humidity_suffix = "%"
        wind_speed_suffix = MessageFactory.__get_wind_speed_suffix__(weather.measurement_system)

        temperature_text = str(round(weather.temperature)) + temperature_suffix
        humidity_text = str(weather.humidity) + humidity_suffix
        wind_speed_text = str(round(weather.wind_speed)) + wind_speed_suffix

        if should_help:
            maximum_presence_length = 15
            promotion_text = "!discloud"
            spaces = " " * (maximum_presence_length - len(temperature_text) - len(promotion_text))
            msg = "{}{}{}".format(temperature_text, spaces, promotion_text)
        else:
            msg = "{}  {}  {}".format(temperature_text, humidity_text, wind_speed_text)

        return msg

    @staticmethod
    def format_help() -> str:
        msg = "discloud: the weather on your discord server!\n"
        msg += "\n"
        msg += "- `!weather [location]` to obtain the current weather at the provided (optional) location\n"
        msg += "- `!forecast [location]` to obtain the weather forecast at the provided (optional) location\n"
        msg += "\n"
        msg += "http://github.com/mbouchenoire/discloud"

        return msg
