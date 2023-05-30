from functools import cache

from Classes.tomls import Config, Emojis

__all__ = (
    "emojis",
    "config",
)


@cache
def emojiration():
    return Emojis("Assets/utils/emojis.toml")


emojis: Emojis = emojiration()


@cache
def configuration():
    return Config("config.toml")


config: Config = configuration()
