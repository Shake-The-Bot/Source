from functools import lru_cache
from os import path
from typing import Any, Dict, Literal, NamedTuple

import toml

from Extensions.extensions import extensions

__all__ = ("config", "Config")


class Webhooks(NamedTuple):
    id: str
    token: str
    type: Literal["servers", "votes"]

    @property
    def link(self) -> str:
        return f"https://discord.com/api/webhooks/{self.id}/{self.token}"


class Config:
    __slots__ = {
        "embed",
        "botlists",
        "values",
        "bot",
        "database",
        "path",
        "client",
        "crowdin",
        "auth",
    }

    def __init__(self, _path):
        self.path = _path
        if not path.exists(self.path):
            raise AttributeError(self.path)
        self.values = toml.load(self.path)
        self.reload()

    def reload(self):
        self.values = toml.load(self.path)
        self.setattr()

    def setattr(self):
        for section in self.__slots__:
            if section in ["path", "values"]:
                continue
            if not self.values.get(section):
                raise AttributeError(
                    f"In der Konfiguration fehlt die '{section}' Sektion."
                )
        self.bot = Bot(self.values["bot"], self.values["version"])
        self.client = Client(self.values["client"])
        self.database = Database(self.values["database"])
        self.botlists = BotLists(self.values["botlists"])
        self.auth = Authentication(self.values["auth"])
        self.crowdin = self.values["crowdin"].get("url")
        self.embed = Embed(
            self.values["embed"],
            self.bot.authentication,
            self.bot.server,
            self.botlists.topgg_vote,
            self.bot.donate,
        )


class Database:
    __slots__ = {"postgresql", "database", "user", "password", "port"}

    def __init__(self, values) -> Dict[str, Any]:
        self.database = values.get("database", None)
        self.user = values.get("user", None)
        self.password = values.get("password", None)
        self.port = values.get("port", None)
        self.postgresql = "postgresql://{us}:{pw}@localhost:{port}/".format(
            pw=self.password, port=self.port, us=self.user
        )


class Client:
    __slots__ = {"token", "retries", "id", "extensions", "shard", "shard_count"}

    def __init__(self, values) -> Dict[str, Any]:
        self.shard = values.get("shard", False)
        self.shard_count = values.get("shard_count", 1)
        self.extensions = extensions
        self.token = values.get("token", None)
        self.id = values.get("id", None)
        self.retries = values.get("retries", 1)


class Bot:
    __slots__ = {
        "owner_ids",
        "authentication",
        "server",
        "donate",
        "server_id",
        "presence",
        "version",
        "description",
        "prefix",
        "webhooks",
    }

    def __init__(self, values, version) -> Dict[str, Any]:
        self.presence = values.get("presence", ["listening", "/help"])
        self.description = "discord bot written with discord.py"
        self.donate = values.get("donate", None)
        self.prefix = (
            values.get("prefix", None)
            if isinstance(values.get("PREFIX", ["!"]), list)
            else [values.get("PREFIX")]
        )
        self.owner_ids = values.get("owner_ids", None)
        self.webhooks = [
            Webhooks(value[0], value[1], value[2]) for value in values.get("webhooks")
        ]
        self.version = self.Version(version)
        self.authentication = values.get("authentication", None)
        self.server = values.get("server", None)
        self.server_id = 806512925678370867

    class Version:
        __slots__ = {
            "minor",
            "major",
            "micro",
            "releaselevel",
        }

        def __init__(self, values) -> Dict[str, Any]:
            self.releaselevel = values.get("releaselevel", None)
            self.major = values.get("major", None)
            self.micro = values.get("micro", None)
            self.minor = values.get("minor", None)


class Authentication:
    __slots__ = {
        "twitter",
        "spotify",
        "hastebin",
        "topgg",
        "reddit",
        "statcord",
    }

    def __init__(self, values: dict) -> None:
        specific = lambda sw: dict(
            (key.removeprefix(sw), value)
            for key, value in values.items()
            if key.startswith(sw)
        )
        self.twitter = self.Twitter(specific("twitter_"))
        self.spotify = self.Spotify(specific("spotify_"))
        self.hastebin = self.Hastebin(specific("hastebin_"))
        self.topgg = self.Topgg(specific("topgg_"))
        self.reddit = self.Reddit(specific("reddit_"))
        self.statcord = self.Statcord(specific("statcord_"))

    class Statcord:
        __slots__ = {"key"}

        def __init__(self, values) -> Dict[str, Any]:
            self.key = values.get("key", None)

    class Reddit:
        __slots__ = {"client_id", "client_secret", "username", "password"}

        def __init__(self, values) -> Dict[str, Any]:
            self.client_id = values.get("client_id", None)
            self.client_secret = values.get("client_secret", None)
            self.username = values.get("username", None)
            self.password = values.get("password", None)

    class Topgg:
        __slots__ = {"token", "route", "webhook", "password"}

        def __init__(self, values) -> Dict[str, Any]:
            self.token = values.get("token", None)
            self.webhook = values.get("webhook", None)
            self.route = values.get("/dblwebhook", None)
            self.password = values.get("password", None)

    class Hastebin:
        __slots__ = {"token"}

        def __init__(self, values) -> Dict[str, Any]:
            self.token = values.get("token", None)

    class Spotify:
        __slots__ = {"secret", "id"}

        def __init__(self, values) -> Dict[str, Any]:
            self.secret = values.get("secret", None)
            self.id = values.get("id", None)

    class Twitter:
        __slots__ = {
            "api_key",
            "api_key_secret",
            "bearer_token",
            "users",
            "access_token",
            "access_token_secret",
        }

        def __init__(self, values) -> Dict[str, Any]:
            self.api_key = values.get("api_key", None)
            self.api_key_secret = values.get("api_key_secret", None)
            self.access_token = values.get("access_token", None)
            self.bearer_token = values.get("bearer_token", None)
            self.access_token_secret = values.get("access_token_secret", None)
            self.users = values.get("users", None)


class BotLists:
    __slots__ = {
        "topgg",
        "topgg_vote",
        "discordbotlist",
        "discordbotlist_vote",
        "botlisteu",
        "botlisteu_vote",
        "infinitybots",
        "infinitybots_vote",
        "discordbots",
        "discords",
    }

    def __init__(self, values) -> Dict[str, Any]:
        self.topgg = values.get("topgg", None)
        self.topgg_vote = self.topgg + "/vote"

        self.discordbotlist = values.get("discordbotlist", None)
        self.discordbotlist_vote = self.discordbotlist + "/upvote"

        self.botlisteu = values.get("discord-botlist", None)
        self.botlisteu_vote = self.botlisteu.replace("bots", "vote")

        self.infinitybots = values.get("infinitybots", None)
        self.infinitybots_vote = self.infinitybots + "/vote"

        self.discordbots = values.get("discordbots", None)

        self.discords = values.get("link", None)


class Embed:
    __slots__ = {
        "color",
        "colour",
        "hex_color",
        "hex_colour",
        "error_color",
        "error_colour",
        "hex_error_color",
        "hex_error_colour",
        "hex_error_color",
        "footer",
    }

    def __init__(self, values, authentication, server, vote, donate) -> Dict[str, Any]:
        self.color = self.colour = values.get("colour", None)
        self.hex_color = self.hex_colour = values.get("hex_colour", None)
        self.error_color = self.error_colour = values.get("error_colour", None)
        self.hex_error_color = self.hex_error_colour = values.get(
            "hex_error_colour", None
        )

        from Classes.i18n import _
        from Classes.types import Format

        self.footer = Format.bold(
            "・".join(
                [
                    _("[Invite]({authentication})").format(
                        authentication=authentication
                    ),
                    _("[Support]({server})").format(server=server),
                    _("[Vote]({vote})").format(vote=vote),
                    _("[Shake+]({donate})").format(donate=donate),
                ]
            )
        )


@lru_cache()
def configuration():
    return Config("config.toml")


config: Config = configuration()
