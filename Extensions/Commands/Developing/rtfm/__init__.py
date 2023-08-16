############
#
import asyncio
from asyncio import create_task
from collections import defaultdict, deque
from contextlib import suppress
from difflib import get_close_matches
from importlib import reload
from typing import List, Optional

import cchardet
from bs4 import BeautifulSoup
from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale
from Classes.helpful import ResultFuture
from Classes.types import DocItem, Modules, QueueItem
from Classes.useful import fetch_inventory, markdown
from discord import Interaction, PartialEmoji, app_commands
from discord.app_commands import Choice, choices
from discord.ext.commands import guild_only, hybrid_command, is_owner

from ..developing import Developing
from . import rtfm, testing

########
#

RELATIVE = defaultdict[str, list[DocItem]]


class rtfm_extension(Developing):
    queue: deque[QueueItem] = deque()
    parsing: Optional[asyncio.Task] = None
    todo: RELATIVE = defaultdict(list)
    """
    rtfm_cog
    """

    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)

        try:
            reload(rtfm)
        except:
            pass

        self.futures: dict[DocItem, ResultFuture] = defaultdict(ResultFuture)

        bot.cache.setdefault("soups", dict())
        self.soups: dict[str, BeautifulSoup] = bot.cache["soups"]

        bot.cache.setdefault("symbols", dict())
        self.symbols: dict[Modules, dict[str, DocItem]] = bot.cache["symbols"]
        self.names: dict[Modules, dict[str, DocItem]] = dict()

    @property
    def display_emoji(self) -> str:
        return PartialEmoji(name="\N{BOOKS}")

    async def cog_load(self):
        await self.refresh()

    async def refresh(self):
        # self.symbols.clear()
        # self.soups.clear()
        if not self.symbols:
            coros = [self.scrape(module) for module in Modules]
            await asyncio.gather(*coros)

    async def rtfm_slash_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        if not bool(self.symbols["symbols"]):
            await interaction.response.autocomplete([])
            await self.refresh()
            return []

        if not current:
            return [
                app_commands.Choice(name=m, value=m)
                for m in self.bot.cache["rtfm"]["Python"][:25]
            ]

        assert interaction.command is not None

        key = getattr(interaction.namespace, "key", "Python")
        # if not key in self.symbols:
        #     self.symbols[key] = await build_lookup_table(
        #         self.bot.session, key
        #     )

        items = self.symbols[key]

        matches: Optional[List[str]] = get_close_matches(current, items)
        if bool(matches):
            return [app_commands.Choice(name=m, value=m) for m in matches]

        if current in items:
            return [app_commands.Choice(name=current, value=current)]
        else:
            return []

    @hybrid_command(name="rtfm")
    @guild_only()
    @setlocale()
    @is_owner()
    @choices(key=[Choice(name=m.name.capitalize(), value=m.name) for m in Modules])
    @app_commands.autocomplete(entity=rtfm_slash_autocomplete)
    @locale_doc
    async def rtfm(
        self,
        ctx: ShakeContext,
        key: Optional[str] = None,
        *,
        entity: Optional[str] = None,
    ) -> None:
        _(
            """View objects from certain documentation.

            RTFM is internet slang for the phrase "read the damn manual".
            This also applies to this command, with the help of which you can get the URLs to the documentation for various things

            Parameters
            -----------
            key: Optional[str]
                the module (Python, Discord, ...). 
                Defaults to ``Python``

            entity: Optional[str]
                the thing you want to get information about (getattr, ctx.command, ...). 
                Defaults to ``None`` and returning the ``key`` website url
            """
        )
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else rtfm

        try:
            default = Modules["Python"]
            if key is None:
                module = default
            else:
                try:
                    lowered = key.lower()
                    module: Modules = {m.name.lower(): m for m in Modules}[lowered]
                except KeyError:
                    if entity is None:
                        entity = key
                        module = default
                    else:
                        return await ctx.send(
                            "Wrong key... know what you do!", ephemeral=True
                        )

            assert module
            await do.command(ctx).__await__(module, entity)

        except:
            if ctx.testing:
                raise Testing
            raise

    @hybrid_command(name="rtfms")
    @guild_only()
    @setlocale()
    @is_owner()
    @locale_doc
    async def rtfms(self, ctx: ShakeContext) -> None:
        _("""View all modules""")
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else rtfm

        try:
            await do.command(ctx).rtfms()

        except:
            if ctx.testing:
                raise Testing
            raise

    async def scrape(self, module: Modules) -> RELATIVE:
        self.symbols.setdefault(module.name, dict())
        self.names.setdefault(module.name, dict())
        inventory: RELATIVE = await fetch_inventory(self.bot.session, module)
        await self.single(module, inventory)

    async def single(self, module: Modules, inventory: RELATIVE):
        for relative, items in inventory.items():
            self.todo[relative].extend(items)
            for item in items:
                self.symbols[module.name][item.id.lower()] = item
                self.names[module.name][item.name.lower()] = item

    async def get_markdown(self, item: DocItem):
        markdown = item.markdown

        if markdown is None:
            try:
                markdown = await self.fetch_markdown(item)
            except Exception as e:
                self.bot.log.warning(
                    f"A error has occurred when requesting parsing of {item}.",
                    exc_info=e,
                )
                return "Unable to parse the requested symbol due to an error."

            if markdown is None:
                return "Requested symbol cant be parsed."

        return markdown

    async def fetch_markdown(self, item: DocItem, alone: bool = False):
        if item not in self.futures and item not in self.queue:
            self.futures[item].requested = True

            soup = await self.get_soup(item)
            qitem = QueueItem(item, soup)
            queue = [QueueItem(item, soup) for item in self.todo[item.relative]]
            queue.append(qitem)
            self.queue.extendleft(queue)
            if not self.parsing:
                self.parsing = create_task(self.parse())
        else:
            qitem = None
            self.futures[item].requested = True
        if qitem:
            self.bot.log.debug("mooving it to the front")
            with suppress(ValueError):
                self.move_to_front(qitem)

        return await self.futures[item]

    async def get_soup(self, item: DocItem):
        if soup := self.soups.get(item.relative_url):
            return soup
        else:
            self.bot.log.debug("requesting site")
            async with self.bot.session.get(
                item.relative_url, raise_for_status=True
            ) as response:
                self.bot.log.debug("done requesting site")
                if response.status != 200:
                    return None
                text = await response.text(encoding="utf8")
            self.bot.log.debug("Parsing site")
            soup = await self.bot.loop.run_in_executor(
                None,
                BeautifulSoup,
                await response.text(encoding="utf8"),
                "lxml",
            )
            self.bot.log.debug("done parsing site")

            self.soups[item.relative_url] = soup
            return soup

    async def parse(self):
        done = 0
        marked = 0

        self.bot.log.debug("Started parsing")
        while self.queue:
            item, soup = self.queue.pop()

            if (future := self.futures[item]).done():
                continue
            result = await markdown(item, soup)

            assert result
            item.markdown = result

            done += 1
            future.set_result(result)
            del self.futures[item]
            await asyncio.sleep(0)

        self.bot.log.debug(f"Ended parsing ({marked}/{done} items)")
        self.parsing = None

    def move_to_front(self, item: QueueItem | DocItem) -> None:
        index = self.queue.index(item)
        item = self.queue[index]
        del self.queue[index]
        self.queue.append(item)

    async def clear(self) -> None:
        """
        Clear all internal symbol data.

        Wait for all user-requested symbols to be parsed before clearing the parser.
        """
        for future in filter(
            lambda f: getattr(f, "user_requested", False), self._item_futures.values()
        ):
            await future
        if self.parsing is not None:
            self.parsing.cancel()
        self.queue.clear()
        self.futures.clear()


async def setup(bot: ShakeBot):
    await bot.add_cog(rtfm_extension(bot))


#
############
