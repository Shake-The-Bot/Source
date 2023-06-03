############
#
from asyncio import run, set_event_loop_policy
from contextlib import contextmanager
from json import dumps, loads
from logging import INFO, NullHandler, getLogger
from traceback import print_exc
from typing import Literal

from asyncpg import Connection, Pool, connect, create_pool
from click import Choice, echo, group, option, pass_context, secho, style
from discord import Activity, ActivityType, Intents

from Classes import (
    Migration,
    NoCommands,
    NoShards,
    OnlyCommands,
    ShakeBot,
    config,
    ensure_uri_can_run,
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

        file, stream = handler(
            file=True,
            stream=True,
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
        log.addFilter(NoShards)

    for func in (root, commands, discord):
        func()
    yield


async def _create_pool(type: Literal["guild", "bot"] = "bot") -> Pool:
    def _encode_jsonb(value):
        return dumps(value)

    def _decode_jsonb(value):
        return loads(value)

    async def init(con):
        await con.set_type_codec(
            "jsonb",
            schema="pg_catalog",
            encoder=_encode_jsonb,
            decoder=_decode_jsonb,
            format="text",
        )

    await ensure_uri_can_run(config=config, type=type)
    return await create_pool(
        config.database.postgresql + type,
        init=init,
        command_timeout=60,
        max_size=20,
        min_size=20,
    )


async def run_bot():
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
        bot.pool: Pool = await _create_pool("bot")
        bot.gpool: Pool = await _create_pool("guild")
        await bot.start(token=config.client.token)


@group(invoke_without_command=True, options_metavar="[options]")
@pass_context
def main(ctx):
    """Launches the bot."""
    if ctx.invoked_subcommand is None:
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
        run(run_bot())


@main.group(short_help="database stuff", options_metavar="[options]")
def db():
    pass


@db.command()
@option(
    "-t",
    "--type",
    help="type of revision",
    default="bot",
    type=Choice(["guild", "bot"]),
)
@option(
    "--reason", "-r", help="The reason for this revision.", default="Initial migration"
)
def init(reason, type: Literal["guild", "bot"]):
    """Initializes the database and creates the initial revision."""

    run(ensure_uri_can_run(config=config, type=type))

    migration = Migration(type=type)
    revision = migration.create_revision(reason)
    echo(f"created revision V{revision.version!r}")
    secho(f"hint: use the `upgrade` command to apply", fg="yellow")


@db.command()
@option(
    "--type",
    "-t",
    default="bot",
    help="type of revision",
    type=Choice(["guild", "bot"]),
)
@option("--reason", "-r", help="The reason for this revision.", required=True)
def migrate(reason, type: Literal["guild", "bot"] = "bot"):
    """Creates a new revision for you to edit."""
    migration = Migration(type=type)
    if migration.is_next_revision_taken():
        echo("an unapplied migration already exists for the next version, exiting")
        secho("hint: apply pending migration with the `upgrade` command", bold=True)
        return

    revision = migration.create_revision(reason)
    echo(f"Created revision V{revision.version!r}")


async def run_upgrade(migration: Migration) -> int:
    connection: Connection = await connect(migration.using_uri)  # type: ignore
    return await migration.upgrade(connection)


@db.command()
@option("--sql", help="Print the SQL instead of executing it", is_flag=True)
@option(
    "--type",
    "-t",
    default="bot",
    help="type of revision",
    type=Choice(["guild", "bot"]),
)
def upgrade(sql, type: Literal["guild", "bot"] = "bot"):
    """Upgrades the database at the given revision (if any)."""
    migration = Migration(type=type)

    if sql:
        migration.display()
        return

    try:
        applied = run(run_upgrade(migration))
    except Exception:
        print_exc()
        secho("failed to apply migration due to error", fg="red")
    else:
        secho(f"Applied {applied} revisions(s)", fg="green")


@db.command()
def current():
    """Shows the current active revision version"""
    migration = Migration()
    echo(f"Version {migration.version}")


@db.command()
@option("--reverse", help="Print in reverse order (oldest first).", is_flag=True)
def log(reverse):
    """Displays the revision history"""
    migration = Migration()
    # Revisions is oldest first already
    revs = (
        reversed(migration.ordered_revisions)
        if not reverse
        else migration.ordered_revisions
    )
    for rev in revs:
        as_yellow = style(f"V{rev.version:>03}", fg="yellow")
        echo(f'{as_yellow} {rev.description.replace("_", " ")}')


if __name__ == "__main__":
    logger = getLogger()
    with setup():
        main()
