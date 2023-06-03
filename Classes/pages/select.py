from typing import TYPE_CHECKING, Any, Optional

from discord import Interaction, PartialEmoji, ui, utils

from Classes import _
from Classes.pages.page import Pages
from Classes.pages.source import FrontPageSource, ListPageSource

Group = Item = Any

if TYPE_CHECKING:
    from Classes import MISSING, ShakeBot, ShakeContext
    from Classes.pages import CategoricalMenu
else:
    MISSING = None
    CategoricalMenu = Pages
    from discord.ext.commands import Bot as ShakeBot
    from discord.ext.commands import Context as ShakeContext

__all__ = ("CategoricalSelect",)


class CategoricalSelect(ui.Select):
    view: CategoricalMenu

    def __init__(
        self, ctx: ShakeContext, source: ListPageSource, describe: Optional[bool] = True
    ):
        super().__init__(
            placeholder=_("Choose a Category..."),
            min_values=1,
            max_values=1,
            row=0,
        )
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.find = dict()
        self.source: ListPageSource = source
        self.__categories: Optional[dict[Group, list[Item]]] = None
        self.describe: Optional[bool] = describe

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        self.__fill_options()
        return self

    @property
    def categories(self) -> dict[Group, list[Item]]:
        return self.__categories

    @categories.setter
    def categories(self, value: Any):
        self.__categories = value

    def getter(self, group: Group, attribute: str):
        if not hasattr(group, attribute):
            return None

        attr = None
        unknown = getattr(group, attribute)
        if callable(unknown):
            attr = unknown()
        else:
            attr = unknown

        return attr

    def __fill_options(self) -> None:
        assert self.categories is not None
        self.add_option(
            label=_("Back"),
            emoji=PartialEmoji(name="left", id=1033551843210579988),
            value="shake_back",
        )
        for group in self.categories.keys():
            value = getattr(group, "qualified_name", str(group))
            self.find[value] = group

            label = self.getter(group, "label")

            d = self.getter(group, "describe")
            describe = d if d else self.describe

            emoji = self.getter(group, "emoji")

            d = self.getter(group, "description")
            description = d.split("\n", 1)[0] if d else None

            self.add_option(
                label=label or "<LABEL NOT FOUND>",
                value=value,
                description=description if self.describe and describe else None,
                emoji=emoji,
            )

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        assert self.categories is not None
        value = self.values[0]
        if value == "shake_back":
            if isinstance(self.view.source, FrontPageSource):
                if self.view.page == 0:
                    await interaction.response.defer()
                    await utils.maybe_coroutine(
                        self.view.on_stop, interaction=interaction
                    )
                else:
                    await self.view.rebind(
                        self.view.front(), 0, interaction=interaction
                    )
            else:
                await self.view.rebind(self.view.front(), interaction=interaction)
        else:
            group = self.find.get(value, MISSING)
            items = self.categories.get(group, MISSING)

            if any(_ is MISSING for _ in (group, items)):
                await interaction.response.send_message(
                    _("This category either does not exist or has no items for you."),
                    ephemeral=True,
                )
                return

            source = self.source(
                ctx=self.ctx, group=group, items=items, interaction=interaction
            )
            self.view.cache["source"] = self.view.cache["page"] = None
            await self.view.rebind(source, interaction=interaction)
