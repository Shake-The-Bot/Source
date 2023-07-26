from __future__ import annotations

from typing import List

from discord import PartialEmoji

from Classes import MISSING, Format, Locale, Localization, ShakeCommand, ShakeEmbed, _
from Classes.accessoires import ListMenu, ListPageSource

########
#


class command(ShakeCommand):
    def get_locale_by_name(self, name: str) -> str:
        if found := self.bot.locales.codes.get(name.lower(), MISSING):
            return found.locale

        if found := self.bot.locales.languages.get(name.lower(), MISSING):
            return found.locale

        if found := self.bot.locales.simples.get(name.lower(), MISSING):
            return found.locale

        if found := self.bot.locales.unique_two_letters.get(name.lower(), MISSING):
            return found.locale

        print(self.bot.locales.unique_two_letters)
        return None

    async def set_locale(self, name, guild: bool = False):
        await self.ctx.defer()
        locale = self.get_locale_by_name(name)
        if locale is None:
            description = Format.join(
                _("Your given language is not valid."),
                _("Use {command} to get a list of all available languages").format(
                    command=Format.codeblock("/languages")
                ),
                splitter="\n",
            )
            embed = ShakeEmbed.to_error(self.ctx, description=description)
        elif not locale in self.bot.i18n.locales:
            embed = ShakeEmbed.to_error(
                self.ctx,
                description=_(
                    "I'm sorry to say that I dont have your given locale ready."
                ),
            )
            embed.description += "\n" + _(
                "Try to contribute [here]({link}) if you want to!"
            ).format(link=self.bot.config.auth.crowdin.url)
            locale = None
        else:
            if guild:
                await self.bot.i18n.set_guild(self.ctx.guild.id, locale)
            else:
                await self.bot.i18n.set_guild(self.ctx.author.id, locale)

            embed = ShakeEmbed.to_success(
                self.ctx,
                description=_("{name} was successfully set as language!").format(
                    name=Format.quote(
                        Localization.available[locale]["language"].capitalize()
                    )
                ),
            )
        await self.ctx.chat(embed=embed)
        return

    async def list(self):
        code = await self.bot.i18n.get_user(self.ctx.author.id, default="en-US")
        current: Locale = self.bot.locales.codes.get(code.lower())
        assert current is not None

        menu = ListMenu(
            ctx=self.ctx,
            source=PageSource(
                ctx=self.ctx,
                items=list(self.bot.locales),
                title=_("Available Translations"),
                description=Format.join(
                    _(
                        "There are currently translations for `{languages}` languages\nand your current language is {current}.".format(
                            languages=Format.codeblock(len(self.bot.locales)),
                            current=Format.bold(current.language),
                        )
                    ),
                    Format.italics(
                        _(
                            "Don't you see your language or is it incomplete?\nThen come help us out on [Crowdin]({link})!"
                        ).format(
                            link=self.bot.config.crowdin,
                        )
                    ),
                    splitter="\n\n",
                ),
            ),
        )
        await menu.setup()
        await menu.send(ephemeral=True)


class PageSource(ListPageSource):
    def add_field(self, embed, item: Locale):
        index = Format.codeblock(f" {self.items.index(item) + 1}. ")
        split = "\N{EM DASH}"

        specified = item.specific
        if specified:
            language = specified.capitalize()
        else:
            language = item.language.capitalize()

        if str(item) == str(self.kwargs.get("current", MISSING)):
            tick = str(PartialEmoji(name="left", id=1033551843210579988))
        else:
            tick = ""

        embed.add_field(
            inline=False,
            name=" ".join(
                (
                    index,
                    item.flag,
                    split,
                    Format.codeblock(language),
                    tick,
                )
            ),
            value=Format.multicodeblock(
                ", ".join(
                    (
                        item.locale,
                        language,
                        item.simplified,
                    )
                )
            ),
        )


#
############
