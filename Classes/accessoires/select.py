from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple, Union

from discord import Emoji, Interaction, PartialEmoji, SelectOption, ui, utils
from discord.utils import maybe_coroutine

from Classes.accessoires.page import ShakePages
from Classes.accessoires.source import FrontPageSource, ListPageSource
from Classes.i18n import _
from Classes.useful import MISSING

Group = Item = Any

if TYPE_CHECKING:
    from Classes import ShakeBot, ShakeContext

__all__ = ("CategoricalSelect",)


class Selects:
    label: str
    value: str
    description: Optional[str]
    emoji: Optional[Union[str, Emoji, PartialEmoji]]
    default: bool

    def __init__(
        self,
        label=MISSING,
        value=MISSING,
        description=MISSING,
        emoji=MISSING,
        default=MISSING,
        /,
        options: List = MISSING,
    ) -> None:
        if any(
            not _ is MISSING for _ in (label, value, description, emoji, default)
        ) and bool(options):
            raise ValueError("Can't pass options and other kwargs too")
        pass


class CategoricalSelect(ui.Select):
    view: ShakePages

    def __init__(
        self,
        ctx: ShakeContext,
        source: ListPageSource,
        describe: Optional[bool] = True,
        **kwargs: Any,
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
        for k, v in kwargs.items():
            setattr(self, k, v)

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
            value="ShakeBack",
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
        if value == "ShakeBack":
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
