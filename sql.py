from asyncio import run
from traceback import print_exc
from typing import Literal

from click import Choice, echo, group, option, pass_context, secho, style

from Classes import Migration, config


@group(invoke_without_command=False, options_metavar="[options]")
@pass_context
def main(ctx):
    """Setup some sql stuff"""
    ...


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

    run(Migration.ensure_uri_can_run(config=config, type=type))

    migration = Migration(type=type)
    revision = migration.create_revision(reason)
    echo(f"created revision V{revision.version!r}")
    secho(f"use the `upgrade` command to apply", fg="yellow", italic=True)


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
        secho(
            "apply pending migration with the `upgrade` command",
            fg="yellow",
            italic=True,
        )
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
    main()
