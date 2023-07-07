############
#
from asyncio import run, set_event_loop_policy
from contextlib import contextmanager
from logging import INFO, NullHandler, getLogger

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
        return ["<@!{}> ".format(bot.user.id), "<@{}> ".format(bot.user.id)]

    async with ShakeBot(
        shard_count=2,
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
    with setup():
        try:
            run(main())
        except:
            exit()
