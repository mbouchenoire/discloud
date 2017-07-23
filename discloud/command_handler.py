import datetime
import discord
from .settings import TemperatureSettings
from .weather import OwmWeatherService
from .embed_weather import OwmEmbedWeatherFactory


class CommandHandler(object):
    _INVALID_COMMAND_FORMAT_MSG = "the weather command format must be '!weather <offset>@<place>'" \
                                      " (e.g. !weather +1@Nantes)"
    _INVALID_OSSET_MSG = "the forecast daily offset must be >= 0"
    _MISSING_PLACE_MSG = "the place is mandatory (@<place>)"

    _VALID_COMMAND_PREFIXES = ["!weather", "weather", "!meteo", "meteo"]

    def __init__(self,
                 owm_weather_service: OwmWeatherService,
                 temperature_settings: TemperatureSettings,
                 discord_client: discord.Client):
        self._owm_weather_service = owm_weather_service
        self._temperature_settings = temperature_settings
        self._discord_client = discord_client

    async def handle(self, command) -> None:
        content = command.content

        if not any(content.startswith(prefix) for prefix in CommandHandler._VALID_COMMAND_PREFIXES):
            return None

        for valid_prefix in CommandHandler._VALID_COMMAND_PREFIXES:
            content = content.replace(valid_prefix, "")

        if "@" not in content:
            return await self._discord_client.send_message(command.channel, CommandHandler._INVALID_COMMAND_FORMAT_MSG)

        parts = content.split("@")

        if len(parts) != 2:
            return await self._discord_client.send_message(command.channel, CommandHandler._INVALID_COMMAND_FORMAT_MSG)

        offset_str = parts[0]
        place = parts[1]

        offset = 0

        if offset_str is not None and offset_str.strip() != "":
            offset = int(offset_str)

            if offset < 0:
                return await self._discord_client.send_message(command.channel, CommandHandler._INVALID_OSSET_MSG)

        if place is None or place == "":
            return await self._discord_client.send_message(command.channel, CommandHandler._MISSING_PLACE_MSG)

        day = datetime.datetime.today() + datetime.timedelta(days=offset)

        embed_weather_factory = OwmEmbedWeatherFactory(self._owm_weather_service,
                                                       day,
                                                       place,
                                                       self._temperature_settings)

        embed_weather = embed_weather_factory.create_embed_weather()

        await self._discord_client.send_message(command.channel, embed=embed_weather)
