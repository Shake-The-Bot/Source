############
#
import sys
from re import compile
from discord import Intents
from contextlib import contextmanager
from click import option, group, argument, pass_context, Context
from Classes.database.db import _create_pool
from Classes import Migration, config
from bot import ShakeBot
from logging import getLogger, INFO
from discord import ActivityType, Activity
from asyncio import set_event_loop_policy, run
from Classes.logging.logger import stream, file_handler, command_handler

try:
    from uvloop import EventLoopPolicy # type: ignore
except ImportError:
    pass
else:
    set_event_loop_policy(EventLoopPolicy())

args = sys.argv[1:]
########
#

logger = getLogger()
REVISION_FILE = compile(r'(?P<kind>current-|)(?P<name>.+).json')
banner = ("\n"
    "   ▄████████▄   ▄██    ██▄     ▄████████   ▄██   ▄██   ▄████████▄ \n"
    "  ███▀    ███   ███    ███    ███    ███   ███ ▄███▀   ███▀   ▄██ \n"
    "  ███      █▀   ███    ███▄▄  ███    ███   ███▐██▀     ███    █▀  \n"
    "  ████▄▄▄▄▄     ███▄▄▄████▀   ███▄▄▄▄███  ▄████▀▀     ▄███▄▄▄     \n"
    "   ▀▀▀▀▀▀███▄ ▄█████▀▀▀███  ▀████▀▀▀▀███ ▀▀█████▄    ▀▀███▀▀▀     \n"
    "          ███   ███    ███    ███    ███   ███▐██▄     ███    █▄  \n"
    "   ▄█   ▄███▀   ███    ███    ███    ███   ███ ▀███▄   ███    ██▄ \n"
    " ▄█████████▀    ▀██    █▀     ███    ██▀   ███   ▀██▄  ██████████ \n"
"\u200b")
########
print(banner)
#

@contextmanager
def setup():
    logger.setLevel(INFO)
    logger.addHandler(stream)
    logger.addHandler(file_handler())
    cmdlogger = getLogger('command')
    cmdlogger.addHandler(command_handler())
    yield
    handlers = logger.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        logger.removeHandler(hdlr)


async def run_bot():
    def prefix(bot, msg):
        return ['<@!{}> '.format(bot.user.id), '<@{}> '.format(bot.user.id)]
    
    async with ShakeBot(
            shard_count=1, command_prefix=prefix, case_insensitive=True, intents=Intents.all(), 
            description=config.bot.description, help_command=None, fetch_offline_members=True, 
            owner_ids=config.bot.owner_ids, strip_after_prefix=True,
            activity=Activity(type=getattr(ActivityType, config.bot.presence[0], ActivityType.playing), name=config.bot.presence[1])
        ) as bot:
        try:
            pool = await _create_pool(config)
        except:
            raise

        bot.pool = pool.get('bot', None)
        bot.config_pool = pool.get('config', None)
        await bot.open(token=config.client.token)


@group(invoke_without_command=True, options_metavar='[options]')
@pass_context
def main(context: Context):
    if context.invoked_subcommand is None:
        with setup():
            run(run_bot())


@main.command()
@option('--reason', '-r', help='The reason for this revision.', default='Initial migration')
@argument('id', metavar='[id]')
def init(id, reason):
    """Initializes the database and creates the initial revision."""
    async def i():
        item = Migration.dbitem(id)
        migrations = Migration(item)
        initiation = await migrations.init(reason)
        logger.info(f'» {item.name} succesfully initiated' if initiation else f'» {item.name} couldn\'t get initiated')
    return run(i())


@main.command()
@option('--reason', '-r', help='The reason for this revision.', default='Initial migration')
@argument('id', metavar='[id]')
def migrate(id, reason):
    """Creates a new revision for you to edit."""
    async def m():
        item = Migration.dbitem(id)
        migrations = Migration(item)
        migration = await migrations.migrate(reason)
        logger.info(f'» {item.name} succesfully migrated' if migration else f'» {item.name} couldn\'t get migrated')
    return run(m())


@main.command()
@option('--reason', '-r', help='The reason for this revision.', default='Initial migration')
@argument('id', metavar='[id]')
def drop(id, reason):
    """Drops a revision for you to edit."""
    async def d():
        item = Migration.dbitem(id)
        migrations = Migration(item)
        drop = await migrations.drop(reason)
        logger.info(f'» {item.name} succesfully dropped' if drop else f'» {item.name} couldn\'t get dropped')
    return run(d())


@main.command()
@option('--reason', '-r', help='The reason for this revision.', default='Initial migration')
@argument('id', metavar='[id]')
def upgrade(id, reason):
    """Upgrades the database at the given revision (if any)."""
    async def u():
        item = Migration.dbitem(id)
        migrations = Migration(item)
        upgrade = await migrations.upgrade(reason)
        logger.info(f'» {item.name} succesfully upgraded' if upgrade else f'» {item.name} couldn\'t get upgraded')
    return run(u())


@main.command()
@option('--reason', '-r', help='The reason for this revision.', default='Initial migration')
@argument('id', metavar='[id]')
def downgrade(id, reason):
    """Downgrades the database at the given revision (if any)."""
    async def d():
        item = Migration.dbitem(id)
        migrations = Migration(item)
        downgrade = await migrations.downgrade(reason)
        logger.info(f'» {item.name} succesfully downgraded' if downgrade else f'» {item.name} couldn\'t get downgraded')
    return run(d())


if __name__ == '__main__':
    main()