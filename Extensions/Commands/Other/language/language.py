from __future__ import annotations

from typing import List

from discord import PartialEmoji

from Classes import MISSING, Format, Locale, Localization, ShakeCommand, ShakeEmbed, _
from Classes.accessoires import ListMenu, ListPageSource

########
#


class command(ShakeCommand):
    def get_locale_by_name(self, name: str, locales: dict[str, Locale]) -> str:
        locs = dict((locale.locale.lower(), locale) for locale in locales.values())
        if found := locs.get(name.lower(), MISSING):
            return found.locale
        languages = dict(
            (locale.language.lower(), locale) for locale in locales.values()
        )
        if found := languages.get(name.lower(), MISSING):
            return found.locale
        simples = dict(
            (locale.simplified.lower(), locale) for locale in locales.values()
        )
        if found := simples.get(name.lower(), MISSING):
            return found.locale

        all_two_letters = dict(
            (locale.two_letters.lower(), locale) for locale in locales.values()
        )
        unique_two_letters = dict(
            (two, locale)
            for two, locale in all_two_letters.items()
            if not list(all_two_letters.keys()).count(two) > 1
        )
        if found := unique_two_letters.get(name.lower(), MISSING):
            return found.locale

        return None

    async def list(self, locales: dict[str, Locale]):
        locale = await self.bot.i18n.get_user(self.ctx.author.id, default="en-US")
        current: Locale = locales.get(locale)

        menu = ListMenu(
            ctx=self.ctx,
            source=PageSource(
                ctx=self.ctx,
                items=list(locales.values()),
                title=_("Available Translations"),
                description=Format.join(
                    _(
                        "There are currently translations for `{languages}` languages\nand your current language is {current}.".format(
                            languages=Format.codeblock(len(locales.keys())),
                            current=Format.bold(current.language),
                        )
                    ),
                    Format.italics(
                        _(
                            "Don't you see your language or is it incomplete?\nThen come help us out on [Crowdin]({link})!"
                        ).format(
                            link=self.bot.config.auth.crowdin.url,
                        )
                    ),
                    splitter="\n\n",
                ),
            ),
        )
        await menu.setup()
        await menu.send(ephemeral=True)

    async def set_locale(self, name, locales: dict[str, Locale], guild: bool = False):
        await self.ctx.defer()
        locale = self.get_locale_by_name(name, locales)
        if locale is None:
            description = Format.join(
                _("Your given language is not valid."),
                _("Use {command} to get a list of all available languages").format(
                    command=Format.codeblock("/language list")
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


class PageSource(ListPageSource):
    def add_field(self, embed, item: Locale):
        index = Format.codeblock(f" {self.items.index(item) + 1}. ")
        split = "\N{EM DASH}"

        specified = item.specific
        if specified:
            language = Format.codeblock(specified.capitalize())
        else:
            language = item.language.capitalize()

        if str(item) == str(self.kwargs.get("current", MISSING)):
            tick = str(PartialEmoji(name="left", id=1033551843210579988))
        else:
            tick = ""

        embed.add_field(
            inline=False,
            name=f"{index} {item.flag} {split} {Format.codeblock(language)} {split} {item.simplified} {tick}",
            value=Format.multicodeblock(
                "/language set {locale}".format(locale=item.locale)
            ),
        )


#
############
