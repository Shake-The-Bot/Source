from __future__ import annotations

from logging import Logger, getLogger
from types import ModuleType
from typing import TYPE_CHECKING, Dict, Optional

from asyncpg import Pool
from discord.ext.tasks import loop

from Classes.helpful import BotBase, DatabaseProtocol
from Classes.useful import MISSING, dump

if TYPE_CHECKING:
    from Classes import __version__
else:
    __version__ = MISSING

__all__ = ("ShakeBot",)

############
#


class ShakeBot(BotBase):
    pool: Pool
    gpool: DatabaseProtocol
    logger: Logger

    def __init__(self, logger: Optional[Logger] = None, **options):
        self.log: Logger = logger or getLogger()
        super().__init__(**options)
        self.__version__ = __version__
        if not self.refresh.is_running:
            self.refresh.start()

    @loop(seconds=60.0)
    async def refresh(self):
        self.config.reload()
        self.emojis.reload()

    async def testing_error(
        self, module: Dict[str, ModuleType], error: Exception
    ) -> None:
        self.log.critical(
            "Could not load {name}, will fallback ({type})".format(
                name=module.__file__, type=error.__class__.__name__
            )
        )
        return None

    async def close(self) -> None:
        print()
        self.log.info("Bot is shutting down")
        if self.refresh.is_running():
            self.refresh.stop()
        await super().close()

    async def dump(self, content: str, lang: Optional[str] = "txt") -> Optional[str]:
        dumped = await dump(content=content, session=self.session, lang=lang)
        return dumped


#
############
