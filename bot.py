from logging import Logger, getLogger
from typing import TYPE_CHECKING, Optional, Sequence

from asyncpg import Pool
from discord import Message
from discord.abc import Snowflake
from discord.ext.commands import Cog

from Classes.helpful import BotBase
from Classes.i18n import _
from Classes.reddit import Reddit
from Classes.useful import MISSING
from Classes.useful import dump as _dump

if TYPE_CHECKING:
    from Classes import __version__
else:
    __version__ = MISSING

__all__ = "ShakeBot"
############
#


class ShakeBot(BotBase):
    pool: Pool
    gpool: Pool
    logger: Logger

    def __init__(self, **options):
        self.log: Logger = getLogger()
        super().__init__(**options)
        self.__version__ = __version__

    async def process_commands(self, message: Message) -> None:
        await super().process_commands(message)
        self.config.reload()
        self.emojis.reload()
        return

    async def setup_hook(self):
        self.reddit: Reddit = Reddit()
        return await super().setup_hook()

    async def add_cog(
        self,
        cog: Cog,
        /,
        *,
        override: bool = False,
        guild: Optional[Snowflake] = MISSING,
        guilds: Sequence[Snowflake] = MISSING,
    ) -> None:
        try:
            await super().add_cog(cog, override=override, guild=guild, guilds=guilds)
        except Exception as e:
            self.log.warn('"{}" couldn\'t get loaded: {}'.format(cog, e))
        return

    async def close(self) -> None:
        print()
        self.log.info("Bot is shutting down")
        await self.reddit.reddit.close()
        self.scheduler.shutdown()
        if self.session and not self.session.closed:
            await self.session.close()
        await super().close()

    async def dump(self, content: str, lang: Optional[str] = "txt") -> Optional[str]:
        url = await _dump(content=content, session=self.session, lang=lang)
        return url


#
############
