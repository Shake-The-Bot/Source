############
#
from logging import Filter
from typing import Optional, Tuple

__all__ = ("NoShards", "NoAttemps", "NoVotes", "NoJobs", "NoCommands", "OnlyCommands")


def only(
    names: Optional[str] = None,
    levelnames: Optional[Tuple[str]] = None,
    messages: Optional[Tuple[str]] = None,
):
    class final(Filter):
        def filter(self, record):
            if names and not record.name.lower() in [name.lower() for name in names]:
                return False
            if levelnames and not record.levelname.lower() in [
                levelname.lower() for levelname in levelnames
            ]:
                return False
            if messages and not any(
                msg.lower() in record.msg.lower() for msg in messages
            ):
                return False
            return True

    return final()


def nomore(
    names: Optional[str] = None,
    levelnames: Optional[Tuple[str]] = None,
    messages: Optional[Tuple[str]] = None,
    mute: Optional[bool] = False,
):
    class final(Filter):
        def filter(self, record):
            if mute:
                return False

            steps = list()

            if names:
                if record.name.lower() in [name.lower() for name in names]:
                    steps.append(False)
                else:
                    steps.append(True)

            if levelnames:
                if record.levelname.lower() in [
                    levelname.lower() for levelname in levelnames
                ]:
                    steps.append(False)
                else:
                    steps.append(True)

            if messages:
                if any(msg.lower() in record.msg.lower() for msg in messages):
                    steps.append(False)
                else:
                    steps.append(True)

            if all(_ is False for _ in steps):
                return False
            else:
                return True

    return final()


NoShards = nomore(
    names=("discord.gateway",), levelnames=("INFO",), messages=("shard id",)
)
NoAttemps = nomore(
    names=("lavalink.websocket",),
    levelnames=(
        "WARNING",
        "INFO",
    ),
    messages=(
        "Invalid response",
        "Lavalink is not running",
        "running on a port",
        "Attempting to establish",
        "connection could not",
    ),
)
NoJobs = nomore(
    names=("apscheduler.scheduler"),
    levelnames=("INFO",),
    messages=(
        "Added job",
        "Adding job tentatively",
    ),
)
OnlyCommands = only(names=("shake.commands",))
NoVotes = nomore(
    names=("aiohttp.access",), levelnames=("INFO",), messages=("159.203.105.187",)
)
NoCommands = nomore(names=("shake.commands",))
#
############
