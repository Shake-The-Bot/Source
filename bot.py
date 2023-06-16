from datetime import datetime
from logging import Logger, getLogger
from types import ModuleType
from typing import TYPE_CHECKING, Dict, Optional, Sequence

from discord import Message
from discord.abc import Snowflake
from discord.ext.commands import Cog

from Classes.helpful import BotBase
from Classes.useful import MISSING, dump

if TYPE_CHECKING:
    from Classes import __version__
else:
    __version__ = MISSING

__all__ = ("ShakeBot",)

############
#


class ShakeBot(BotBase):
    logger: Logger

    def __init__(self, **options):
        self.started = datetime.now()
        self.log: Logger = getLogger()
        super().__init__(**options)
        self.__version__ = __version__

    async def process_commands(self, message: Message) -> None:
        await super().process_commands(message)
        self.config.reload()
        self.emojis.reload()
        return

    async def testing_error(
        self, module: Dict[str, ModuleType], error: Exception
    ) -> None:
        self.log.critical(
            "Could not load {name}, will fallback ({type})".format(
                name=module.__file__, type=error.__class__.__name__
            )
        )
        return None

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
        await super().close()

    async def dump(self, content: str, lang: Optional[str] = "txt") -> Optional[str]:
        url = await dump(content=content, session=self.session, lang=lang)
        return url


#
############
