############
#
from asyncio import run, set_event_loop_policy, sleep
from contextlib import contextmanager
from logging import INFO, NullHandler, basicConfig, getLogger
from sys import exc_info
from traceback import format_exception

from asyncpg import Pool
from discord import Activity, ActivityType, Intents

from Classes import (
    Migration,
    NoCommands,
    NoVotes,
    OnlyCommands,
    ShakeBot,
    config,
    handler,
)

try:
    from uvloop import EventLoopPolicy  # type: ignore
except ImportError:
    pass
else:
    set_event_loop_policy(EventLoopPolicy())
########
#


@contextmanager
def setup():
    def root():
        logger.addHandler(NullHandler())
        logger.setLevel(INFO)

        *n, stream = handler(
            file=False,
            stream=True,
            filters=(
                NoCommands,
                NoVotes,
            ),
        )
        file, *n = handler(
            file=True,
            stream=False,
            filepath="./Classes/logging/latest/shake.log",
            filters=(NoCommands,),
        )

        logger.addHandler(stream)
        logger.addHandler(file)

    def commands():
        log = getLogger("shake.commands")

        file_handler, *n = handler(
            file=True,
            stream=False,
            filepath=f"./Classes/logging/latest/commands.log",
            filters=(OnlyCommands,),
        )
        log.addHandler(file_handler)

    def discord():
        log = getLogger("discord.gateway")

    for func in (root, commands, discord):
        func()
    yield


async def main():
    def prefix(bot, msg):
        return (_.format(bot.user.id) for _ in ("<@!{}> ", "<@{}> "))

    async with ShakeBot(
        logger=logger,
        shard_count=config.client.shard_count,
        command_prefix=prefix,
        case_insensitive=True,
        intents=Intents.all(),
        description=config.bot.description,
        help_command=None,
        fetch_offline_members=True,
        owner_ids=config.bot.owner_ids,
        strip_after_prefix=True,
        activity=Activity(
            type=getattr(ActivityType, config.bot.presence[0], ActivityType.playing),
            name=config.bot.presence[1],
        ),
    ) as bot:
        bot.pool: Pool = await Migration._create_pool("bot")
        bot.gpool: Pool = await Migration._create_pool("guild")
        await bot.start(token=config.client.token)


if __name__ == "__main__":
    logger = getLogger()
    with setup():
        print(
            "\n"
            "   ▄████████▄   ▄██    ██▄     ▄████████   ▄██   ▄██   ▄████████▄ \n"
            "  ███▀    ███   ███    ███    ███    ███   ███ ▄███▀   ███▀   ▄██ \n"
            "  ███      █▀   ███    ███▄▄  ███    ███   ███▐██▀     ███    █▀  \n"
            "  ████▄▄▄▄▄     ███▄▄▄████▀   ███▄▄▄▄███  ▄████▀      ▄███▄▄▄     \n"
            "   ▀▀▀▀▀▀███▄ ▄█████▀▀▀███  ▀████▀▀▀▀███ ▀▀█████▄    ▀▀███▀▀▀     \n"
            "          ███   ███    ███    ███    ███   ███▐██▄     ███    █▄  \n"
            "   ▄█   ▄███▀   ███    ███    ███    ███   ███ ▀███▄   ███    ██▄ \n"
            " ▄█████████▀    ▀██    █▀     ███    ██▀   ███   ▀██▄  ██████████ \n"
            "\u200b"
        )

    tries = 0
    while True:
        try:
            run(main())

        except KeyboardInterrupt:
            break

        except Exception as e:
            if tries < config.client.retries:
                try:
                    logger.debug(
                        "Restarting ({}/{})".format(tries, config.client.retries)
                    )
                    tries += 1
                    run(sleep(5))
                except:
                    break
            else:
                exc, value, tb, *_ = exc_info()
                logger.warning(f"Closing: {''.join(format_exception(exc, value, tb))}")
                break
