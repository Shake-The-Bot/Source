############
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from discord import ButtonStyle, File, Interaction, Message, PartialEmoji, ui
from discord.ext.commands.errors import BotMissingPermissions
from discord.ext.menus import PageSource
from discord.utils import maybe_coroutine

from Classes.i18n import _

if TYPE_CHECKING:
    from Classes import ShakeBot, ShakeContext, ShakeEmbed
else:
    from discord import Embed as ShakeEmbed
    from discord.ext.commands import Bot as ShakeBot
    from discord.ext.commands import Context as ShakeContext

__all__ = ("ShakePages",)

firstemoji = PartialEmoji(name="topleft", id=1033551840744312832)
previousemoji = PartialEmoji(name="left", id=1033551843210579988)
nextemoji = PartialEmoji(name="right", id=1033551841964871691)
lastemoji = PartialEmoji(name="topright", id=1033551844703744041)


########
#
class ShakePages(ui.View):
    page: int = 0
    message: Optional[Message] = None
    """ The Base of all interactive ui.View of Shake"""

    def __init__(
        self, source: PageSource, ctx: ShakeContext, timeout: Optional[float] = 180.0
    ):
        super().__init__(timeout=timeout)
        self.source: PageSource = source
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.bot.cache["pages"][self] = dict()
        self.cache = self.bot.cache["pages"][self]
        self.clear_items()
        self.fill()

    def clear_items(self):
        return super().clear_items()

    def fill(self) -> None:
        if self.source.is_paginating():
            self.add_item(self.go_to_first_page)
            self.add_item(self.go_to_previous_page)
            self.add_item(self.stop_pages)
            self.add_item(self.go_to_next_page)
            self.add_item(self.go_to_last_page)

    def embed(self, embed: ShakeEmbed):
        return embed

    async def _get_from_page(self, item: Any) -> Tuple[Dict[str, Any], File]:
        locale = await self.bot.locale.get_user_locale(self.ctx.author.id) or "en-US"
        await self.bot.locale.set_user_locale(self.ctx.author.id, locale)

        value, file = await maybe_coroutine(self.source.format_page, self, item)
        if isinstance(value, dict):
            return value, file
        elif isinstance(value, str):
            return {"content": value, "embed": None}, file
        elif isinstance(value, ShakeEmbed):
            embed = self.embed(embed=value)
            return {"embed": embed, "content": None}, file
        else:
            return {}, file

    async def show_page(self, interaction: Interaction, item: int) -> None:
        self.page = item
        page_source = await self.source.get_page(self.page)
        self.kwargs, self.file = await self._get_from_page(page_source)

        if not self.kwargs:
            return False

        self.update(self.page)
        attachments = (
            (self.file if isinstance(self.file, list) else [self.file])
            if self.file
            else []
        )
        if interaction.response.is_done():
            if self.message:
                await self.message.edit(
                    **self.kwargs, attachments=attachments, view=self
                )
        else:
            await interaction.response.edit_message(
                **self.kwargs, attachments=attachments, view=self
            )

        return True

    def update(
        self, page: Optional[int] = None, timeouted: Optional[bool] = False
    ) -> None:
        self.timeouted = timeouted
        page = page or self.page or 0
        max_pages = self.source.get_max_pages()
        self.stop_pages.label = "\u2003%(pages)-9s\u2003" % {
            "pages": _("Done") + f" ({page+1}/{max_pages})"
        }

        next_page = page + 1 >= max_pages
        self.go_to_next_page.disabled = next_page
        self.go_to_next_page.style = (
            ButtonStyle.grey if next_page else ButtonStyle.blurple
        )

        last_page = page + 2 >= max_pages
        self.go_to_last_page.disabled = last_page
        self.go_to_last_page.style = (
            ButtonStyle.grey if last_page else ButtonStyle.blurple
        )

        previous_page = page <= 0
        self.go_to_previous_page.disabled = previous_page
        self.go_to_previous_page.style = (
            ButtonStyle.grey if previous_page else ButtonStyle.blurple
        )

        first_page = page <= 1
        self.go_to_first_page.disabled = first_page
        self.go_to_first_page.style = (
            ButtonStyle.grey if first_page else ButtonStyle.blurple
        )

        if timeouted:
            for item in self._children:
                item.disabled = True
                if isinstance(item, ui.Button):
                    item.style = ButtonStyle.grey

    async def show_checked_page(self, interaction: Interaction, page: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None:
                await self.show_page(interaction, page)
            elif max_pages > page >= 0:
                await self.show_page(interaction, page)
        except IndexError:
            pass

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user and (
            interaction.user.id == self.ctx.author.id
            or await self.bot.is_owner(interaction.user)
        ):
            return True
        await interaction.response.send_message(
            "This pagination menu cannot be controlled by you, sorry!", ephemeral=True
        )
        return False

    async def on_timeout(self, interaction: Optional[Interaction] = None) -> None:
        self.update(timeouted=True)
        if (
            not interaction
            or not isinstance(interaction, Interaction)
            or interaction.response.is_done()
        ):
            if self.message:
                await self.message.edit(view=self)
        else:
            await interaction.response.edit_message(view=self)

    async def on_stop(self, interaction: Optional[Interaction] = None) -> None:
        try:
            await self.on_timeout()
        except:
            await interaction.delete_original_response()
        finally:
            super().stop()

    async def on_error(
        self, interaction: Interaction, error: Exception, item: ui.Item
    ) -> None:
        self.bot.dispatch("command_error", interaction, error)
        return

    async def setup(
        self, *, content: Optional[str] = None, page: Optional[int] = 0
    ) -> None:
        if not self.ctx.channel.permissions_for(self.ctx.me).embed_links:
            raise BotMissingPermissions(
                ["embed_links"],
                "I do not have embed links permission in this channel.",
            )

        await self.source._prepare_once()
        source_page = await self.source.get_page(page)
        self.kwargs, self.file = await self._get_from_page(source_page)

        if content:
            self.kwargs.setdefault("content", content)

        self.update(page=page)
        self.page = page
        return True

    async def send(self, ephemeral: Optional[bool] = False):
        files = (
            (self.file if isinstance(self.file, list) else [self.file])
            if self.file
            else None
        )
        self.message = await self.ctx.chat(
            files=files,
            view=self,
            **self.kwargs,
            ephemeral=(True if await self.bot.is_owner(self.ctx.author) else False)
            if ephemeral is None
            else ephemeral,
        )

    @ui.button(emoji=firstemoji, style=ButtonStyle.blurple, row=1)
    async def go_to_first_page(self, interaction: Interaction, button: ui.Button):
        await self.show_page(interaction, 0)

    @ui.button(emoji=previousemoji, style=ButtonStyle.blurple, row=1)
    async def go_to_previous_page(self, interaction: Interaction, button: ui.Button):
        await self.show_checked_page(interaction, self.page - 1)

    @ui.button(label=_("Done"), style=ButtonStyle.green, row=1)
    async def stop_pages(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        await self.on_stop(interaction)

    @ui.button(emoji=nextemoji, style=ButtonStyle.blurple, row=1)
    async def go_to_next_page(self, interaction: Interaction, button: ui.Button):
        await self.show_checked_page(interaction, self.page + 1)

    @ui.button(emoji=lastemoji, style=ButtonStyle.blurple, row=1)
    async def go_to_last_page(self, interaction: Interaction, button: ui.Button):
        await self.show_page(interaction, self.source.get_max_pages() - 1)


#
############
