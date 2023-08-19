############
#
from functools import lru_cache
from os import path
from typing import Any, Dict, List, Optional

import toml
from discord import PartialEmoji

__all__ = ("assets", "Assets")


########
#
def formatter(parts: Optional[List[str]] = None, animated: Optional[bool] = False):
    from Classes.useful import MISSING

    if parts is MISSING:
        return "<Err:ENF>"  # EMOJI_NOT_FOUND
    emoji = PartialEmoji(name=parts[0], id=int(parts[1]), animated=animated)
    return emoji


class Assets:
    __slots__ = {
        "path",
        "values",
        "prefix",
        "dice",
        "dot",
        "slash",
        "cross",
        "hook",
        "everyone",
        "animated",
        "no",
        "arrows",
        "yes",
        "help",
        "badges",
        "status",
    }

    def __init__(self, _path):
        self.path = _path
        self.prefix = f"│-"
        if not path.exists(self.path):
            raise AttributeError(self.path)
        self.values = toml.load(self.path)
        self.reload()

    def reload(self):
        self.values = toml.load(self.path)
        self.setattr()
        return self

    def setattr(self):
        for section in self.__slots__:
            if section in [
                "path",
                "values",
                "prefix",
                "dot",
                "no",
                "yes",
                "slash",
                "cross",
                "hook",
            ]:
                continue
            if not self.values.get(section):
                raise AttributeError(
                    f"In der Konfiguration fehlt die '{section}' Sektion."
                )
        messaging = Messaging(self.values["messaging"])
        self.cross = messaging.cross
        self.hook = messaging.hook
        self.slash = messaging.slash
        self.yes = messaging.yes
        self.no = messaging.no
        self.dot = messaging.dot
        self.arrows = Arrows(self.values["arrows"])
        self.everyone = Everyone(self.values["everyone"])
        self.dice = Dice(self.values["dice"])
        self.badges = Badges(self.values["badges"])
        self.status = Status(self.values["status"])
        self.help = Help(self.values["help"])
        self.animated = Animated(self.values["animated"])


class Status:
    __slots__ = {"offline", "idle", "streaming", "dnd", "online"}

    def __init__(self, values) -> Dict[str, Any]:
        from Classes.useful import MISSING

        self.dnd = formatter(values.get("donotdisturb", MISSING))
        self.online = formatter(values.get("online", MISSING))
        self.streaming = formatter(values.get("streaming", MISSING))
        self.idle = formatter(values.get("idle", MISSING))
        self.offline = formatter(values.get("offline", MISSING))


class Messaging:
    __slots__ = {"cross", "hook", "slash", "dot", "no", "yes"}

    def __init__(self, values) -> Dict[str, Any]:
        from Classes.useful import MISSING

        self.cross = formatter(values.get("cross", MISSING))
        self.hook = formatter(values.get("hook", MISSING))
        self.slash = formatter(values.get("slash", MISSING))
        self.dot = formatter(values.get("dot", MISSING))
        self.no = "".join(str(formatter(_)) for _ in values.get("no", MISSING))
        self.yes = "".join(str(formatter(_)) for _ in values.get("yes", MISSING))


class Badges:
    __slots__ = {
        "hypesquad_brilliance",
        "hypesquad_bravery",
        "hypesquad_balance",
        "early_supporter",
        "hypesquad",
        "bug_hunter_level_2",
        "discord_certified_moderator",
        "bug_hunter",
        "partner",
        "bot",
        "verified_bot_developer",
        "staff",
        "moderator",
        "bot_http_interactions",
        "active_developer",
        "subscriber",
        "verified_bot",
    }

    def __init__(self, values) -> Dict[str, Any]:
        from Classes.useful import MISSING

        self.hypesquad_brilliance = formatter(
            values.get("hypesquad_brilliance", MISSING)
        )
        self.hypesquad_bravery = formatter(values.get("hypesquad_bravery", MISSING))
        self.hypesquad_balance = formatter(values.get("hypesquad_balance", MISSING))
        self.early_supporter = formatter(values.get("early_supporter", MISSING))
        self.hypesquad = formatter(values.get("hypesquad", MISSING))
        self.bug_hunter_level_2 = formatter(values.get("bug_hunter_level_2", MISSING))
        self.bug_hunter = formatter(values.get("bug_hunter", MISSING))
        self.partner = formatter(values.get("partner", MISSING))
        self.verified_bot_developer = formatter(
            values.get("verified_bot_developer", MISSING)
        )
        self.staff = formatter(values.get("staff", MISSING))
        self.moderator = formatter(values.get("moderator", MISSING))
        self.bot_http_interactions = formatter(
            values.get("bot_http_interactions", MISSING)
        )
        self.active_developer = formatter(values.get("active_developer", MISSING))
        self.subscriber = formatter(values.get("subscriber", MISSING))
        self.discord_certified_moderator = formatter(
            values.get("discord_certified_moderator", MISSING)
        )
        self.bot = formatter(values.get("bot", MISSING))
        self.verified_bot = "".join(
            str(_)
            for _ in [
                formatter(values.get("verified_bot", MISSING)[0]),
                formatter(values.get("verified_bot", MISSING)[1]),
            ]
        )


class Everyone:
    __slots__ = {"static", "animated"}

    def __init__(self, values) -> Dict[str, Any]:
        self.static = values.get("static", [])
        self.animated = values.get("animated", [])


class Arrows:
    __slots__ = {"right", "mostright", "left", "mostleft"}

    def __init__(self, values) -> Dict[str, Any]:
        from Classes.useful import MISSING

        self.right = formatter(values.get("right", MISSING))
        self.mostright = formatter(values.get("mostright", MISSING))
        self.left = formatter(values.get("left", MISSING))
        self.mostleft = formatter(values.get("mostleft", MISSING))


class Dice:
    __slots__ = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine"}

    def __init__(self, values) -> Dict[str, Any]:
        from Classes.useful import MISSING

        self.one = formatter(values.get("1", MISSING))
        self.two = formatter(values.get("2", MISSING))
        self.three = formatter(values.get("3", MISSING))
        self.four = formatter(values.get("4", MISSING))
        self.five = formatter(values.get("5", MISSING))
        self.six = formatter(values.get("6", MISSING))
        self.seven = formatter(values.get("7", MISSING))
        self.eight = formatter(values.get("8", MISSING))
        self.nine = formatter(values.get("9", MISSING))


class Help:
    __slots__ = {"plus", "beta", "discord", "group", "owner", "permissions"}

    def __init__(self, values) -> Dict[str, Any]:
        from Classes.useful import MISSING

        self.plus = formatter(values.get("plus", MISSING))
        self.beta = formatter(values.get("beta", MISSING))
        self.group = formatter(values.get("group", MISSING))
        self.discord = formatter(values.get("discord", MISSING))
        self.owner = formatter(values.get("owner", MISSING))
        self.permissions = formatter(values.get("permissions", MISSING))


class Animated:
    __slots__ = {"loading"}

    def __init__(self, values) -> Dict[str, Any]:
        from Classes.useful import MISSING

        self.loading = formatter(values.get("loading", MISSING), True)


@lru_cache()
def assetration():
    return Assets("Assets/assets.toml")


assets: Assets = assetration()
#
############
