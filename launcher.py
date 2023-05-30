############
#
from asyncio import run, set_event_loop_policy
from contextlib import contextmanager
from datetime import datetime
from json import dump, dumps, load, loads
from logging import INFO, NullHandler, getLogger
from os import replace
from pathlib import Path
from re import Match, compile, sub
from traceback import print_exc
from typing import Literal, TypedDict
from uuid import uuid4

from asyncpg import Connection, Pool, connect, create_pool
from asyncpg.exceptions import InvalidCatalogNameError
from click import Choice, echo, group, option, pass_context, secho, style
from discord import Activity, ActivityType, Intents

from Classes import MISSING, NoCommands, NoShards, ShakeBot, config, handler

try:
    from uvloop import EventLoopPolicy  # type: ignore
except ImportError:
    pass
else:
    set_event_loop_policy(EventLoopPolicy())
########
#

banner = (
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


@contextmanager
def setup():
    def root():
        logger.addHandler(NullHandler())
        logger.setLevel(INFO)
        file, stream = handler(
            file=True,
            stream=True,
            filepath="./Classes/logging/latest/commands.log",
            filters=(NoCommands,),
        )
        logger.addHandler(stream)
        logger.addHandler(file)

    def commands():
        log = getLogger("shake.commands")
        file_handler, *n = handler(
            file=True, stream=False, filepath=f"./Classes/logging/latest/shake.log"
        )
        log.addHandler(file_handler)

    def discord():
        log = getLogger("discord.gateway")
        log.addFilter(NoShards)

    for func in (root, commands, discord):
        func()
    yield


async def _create_pool(path: Literal["guild", "bot"] = "bot") -> Pool:
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

    return await create_pool(
        config.database.postgresql + path,
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


class Revisions(TypedDict):
    # The version key represents the current activated version
    # So v1 means v1 is active and the next revision should be v2
    # In order for this to work the number has to be monotonically increasing
    # and have no gaps
    version: int
    database_uri: str


REVISION_FILE = compile(
    r"(?P<kind>V|U)(?P<version>[0-9]+)_(?P<type>bot|guild)_(?P<description>.+).sql"
)


class Revision:
    __slots__ = ("kind", "version", "description", "file")

    def __init__(
        self, *, kind: str, version: int, description: str, file: Path
    ) -> None:
        self.kind: str = kind
        self.version: int = version
        self.description: str = description
        self.file: Path = file

    @classmethod
    def from_match(cls, match: Match[str], file: Path):
        return cls(
            kind=match.group("kind"),
            version=int(match.group("version")),
            description=match.group("description"),
            file=file,
        )


class Migration:
    def __init__(
        self,
        type: Literal["guild", "bot"],
        *,
        filename: str = "Migrations/revisions.json",
    ):
        self.filename: str = filename
        self.type: Literal["guild", "bot"] = type
        self.root: Path = Path(filename).parent
        self.revisions: dict[int, Revision] = self.get_revisions()
        self.load()

    def ensure_path(self) -> None:
        self.root.mkdir(exist_ok=True)

    def load_metadata(self) -> Revisions:
        try:
            with open(self.filename, "r", encoding="utf-8") as fp:
                return load(fp)
        except FileNotFoundError:
            return {
                "version": 0,
                "database_uri": MISSING,
            }

    def get_revisions(self) -> dict[int, Revision]:
        result: dict[int, Revision] = {}
        for file in self.root.glob("*.sql"):
            match = REVISION_FILE.match(file.name)
            if match is not None:
                rev = Revision.from_match(match, file)
                result[rev.version] = rev

        return result

    def dump(self) -> Revisions:
        return {
            "version": self.version,
            "database_uri": self.database_uri,
        }

    def load(self) -> None:
        self.ensure_path()
        data = self.load_metadata()
        self.version: int = data["version"]
        self.database_uri: str = data["database_uri"]
        self.using_uri: str = data["database_uri"] + self.type

    def save(self):
        temp = f"{self.filename}.{uuid4()}.tmp"
        with open(temp, "w", encoding="utf-8") as tmp:
            dump(self.dump(), tmp)

        # atomically move the file
        replace(temp, self.filename)

    def is_next_revision_taken(self) -> bool:
        return self.version + 1 in self.revisions

    @property
    def ordered_revisions(self) -> list[Revision]:
        return sorted(self.revisions.values(), key=lambda r: r.version)

    def create_revision(self, reason: str, *, kind: str = "V") -> Revision:
        cleaned = sub(r"\s", "_", reason)
        sql = f"{kind}{self.version + 1}_{self.type}_{cleaned}.sql"
        path = self.root / sql

        stub = (
            f"-- Revises: V{self.version + 1}\n"
            f"-- Creation Date: {datetime.utcnow()} UTC\n"
            f"-- Reason: {reason}\n\n"
        )

        with open(path, "w", encoding="utf-8", newline="\n") as fp:
            fp.write(stub)

        self.save()
        return Revision(
            kind=kind, description=reason, version=self.version + 1, file=path
        )

    async def upgrade(self, connection: Connection) -> int:
        ordered = self.ordered_revisions
        successes = 0
        async with connection.transaction():
            for revision in ordered:
                if revision.version > self.version:
                    sql = revision.file.read_text("utf-8")
                    await connection.execute(sql)
                    successes += 1

        self.version += successes
        self.save()
        return successes

    def display(self) -> None:
        ordered = self.ordered_revisions
        for revision in ordered:
            if revision.version > self.version:
                print(1, revision)
                print(2, revision.file)
                sql = revision.file.read_text("utf-8")
                echo(sql)


@group(invoke_without_command=True, options_metavar="[options]")
@pass_context
def main(ctx):
    """Launches the bot."""
    if ctx.invoked_subcommand is None:
        print(banner)
        run(run_bot())


@main.group(short_help="database stuff", options_metavar="[options]")
def db():
    pass


async def ensure_uri_can_run(type: Literal["guild", "bot"]) -> bool:
    conn: Connection = await connect(config.database.postgresql)
    try:
        connection: Connection = await connect(config.database.postgresql + type)
    except InvalidCatalogNameError:
        try:
            await conn.execute(
                f'CREATE DATABASE "{type}" OWNER "{config.database.user}"'
            )
        except:
            raise
    finally:
        await connection.close()
    await conn.close()
    return True


@db.command()
@option(
    "--type",
    "-t",
    help="type of revision",
    type=Choice(["guild", "bot"]),
    default="guild",
)
@option(
    "--reason", "-r", help="The reason for this revision.", default="Initial migration"
)
def init(reason, type: Literal["guild", "bot"]):
    """Initializes the database and creates the initial revision."""

    run(ensure_uri_can_run(type=type))

    migration = Migration(type=type)
    migration.database_uri = config.database.postgresql
    revision = migration.create_revision(reason)
    echo(f"created revision V{revision.version!r}")
    secho(f"hint: use the `upgrade` command to apply", fg="yellow")


@db.command()
@option(
    "--type",
    "-t",
    help="type of revision",
    type=Choice(["guild", "bot"]),
    default="guild",
)
@option("--reason", "-r", help="The reason for this revision.", required=True)
def migrate(reason, type: Literal["guild", "bot"]):
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
    help="type of revision",
    type=Choice(["guild", "bot"]),
    default="guild",
)
def upgrade(sql, type: Literal["guild", "bot"]):
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
