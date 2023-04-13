############
#
from inspect import cleandoc
from typing import Union
from Classes import ShakeContext, ShakeBot, ShakeEmbed, MISSING
from discord import PartialEmoji
from os import path
from polib import pofile
from contextlib import suppress
from gettext import GNUTranslations
from Classes.pages import ListMenu, ListPageSource
from Classes.i18n import _, localedir, gettext_translations, localess, locales as __locales
########
#

class locale():
    locale: str
    authors: str
    flag: str
    language: str
    two_letters_code: str
    locale_with_underscore: str

    __slots__ = {'locale', 'authors', 'flag', 'language', 'two_letters_code', 'locale_with_underscore'}

    def __init__(self, locale: str) -> None:
        po = None
        with suppress(OSError): 
            po = pofile(path.join(localedir, locale, 'LC_MESSAGES', 'shake.po'))
        y = {'ja': 'jp', 'zn': 'cn'}
        metadata = getattr(po, 'metadata', {})
        crw_lang = metadata.pop('X_Crowdin_Language', '') # ''  /  None
        self.authors = [', '.join(metadata.pop('Last-Translator', '').split())] or []
        self.two_letters_code = metadata.pop('Language', crw_lang[:2] or locale[:2]).lower() # if crw_lang else
        self.language = localess.get(locale, {}).get('language', None) or metadata.pop('Language-Team', None) #.replace(two_letters_code, y.get(two_letters_code, two_letters_code))
        self.flag: str = ':flag_{}:'.format(y.get(code := self.two_letters_code, code))
        self.locale_with_underscore = ((crw_lang.lower()+'_'+crw_lang.upper()) if len(crw_lang) == 2 else (crw_lang)).replace('-', '_') if crw_lang else None
        self.locale = locale

    def __str__(self) -> str:
        return self.locale



class command():
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    def get_locale_by_name(self, name: str) -> str:
        for locale in localess:
            language = localess[locale]['language']
            simplified = localess[locale]['simplified']
            if name in [language, locale] or name in simplified:
                return locale
        return None


    def check(self, locale) -> Union[ShakeEmbed, bool]:
        if not (locale := self.get_locale_by_name(locale)):
            embed = ShakeEmbed.default(self.ctx, description = _("{emoji} {prefix} **Your given language is not valid. Use </language list> to get a list of all available languages**").format(
                emoji=self.bot.emojis.cross, prefix=self.bot.emojis.prefix))
            return embed, None
        if not locale in __locales:
            embed = ShakeEmbed.default(self.ctx, description = _(
                """{emoji} {prefix} **I'm sorry to say that I dont have your given locale ready.**
                Try to contribute [here]({link}) if you want to!""").format(
                emoji=self.bot.emojis.cross, prefix=self.bot.emojis.prefix, link="https://github.com/KidusTV/locales/"))
            return embed, None
        embed = ShakeEmbed.default(self.ctx, description = _(
            """{emoji} {prefix} **The specified language was set successfully!**""").format(
                emoji=self.bot.emojis.hook, prefix=self.bot.emojis.prefix))
        return embed, locale


    async def list(self): 
        locales = [
            locale(x) for x in list(
                x for x, y in gettext_translations.items() if isinstance(y, GNUTranslations)
            )
        ]
        current = locale(await self.bot.locale.get_user_locale(self.ctx.author.id) or 'en-US')
        menu = ListMenu(
            ctx=self.ctx, source=PageSource(
                ctx=self.ctx, items=locales, current=current, title = _("Available Translations"),
                description=_("There are currently translations for `{languages}` languages \nand your current language is **{current}**. \nIs something wrong or don't you see your language? \nCome help us out on [Crowdin]({link})!""")).format(
                    languages=len(locales), link=self.bot.config.other.crowdin, current=current.language
            )
        )
        await menu.setup()
        await menu.send()


    async def user_locale(self, locale):
        await self.ctx.defer()
        embed, locale = self.check(locale)
        if locale:
            await self.bot.locale.set_user_locale(self.ctx.author.id, locale)
        await self.ctx.smart_reply(embed=embed)
        return


    async def guild_locale(self, locale):
        await self.ctx.defer()
        embed, locale = self.check(locale)
        if locale:
            await self.bot.locale.set_guild_locale(self.ctx.guild.id, locale)
        await self.ctx.smart_reply(embed=embed)
        return


class PageSource(ListPageSource):
    def add_field(self, embed, item):
        tick = str(PartialEmoji(name='left', id=1033551843210579988)) if str(item) == str(self.kwargs.get('current', MISSING)) else ''
        embed.add_field(
            inline=False,
            name='` {index}. ` {flag} \N{EM DASH} {language} {emoji}'.format(
                index=self.items.index(item)+1, flag=getattr(item, "flag", ""), 
                language=item.language, emoji=tick
            ), 
            value="""{usage} to set this language""".format(
                authors=', '.join(item.authors) or '`/`', 
                usage=f'`/language set {item.locale}`'
            )
        )
#
############