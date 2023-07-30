############
#
from difflib import get_close_matches
from enum import Enum
from importlib import reload
from os import path
from re import compile
from typing import List, Optional

from discord import Interaction, Member, PartialEmoji, app_commands
from discord.app_commands import Choice, choices
from discord.ext.commands import Greedy, guild_only, hybrid_command, is_owner

from Classes import (
    MISSING,
    Manuals,
    ShakeBot,
    ShakeContext,
    Testing,
    _,
    build_lookup_table,
    locale_doc,
    setlocale,
)

from ..developing import Developing
from . import rtfm, testing

########
#


class rtfm_extension(Developing):
    """
    rtfm_cog
    """

    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(rtfm)
        except:
            pass
        bot.cache.setdefault("rtfm", dict())

    @property
    def display_emoji(self) -> str:
        return PartialEmoji(name="\N{BOOKS}")

    async def cog_load(self):
        self.bot.cache["rtfm"].clear()
        self.bot.cache["rtfm"]["python"] = await build_lookup_table(
            self.bot.session, "python"
        )

    async def rtfm_slash_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        if not bool(self.bot.cache["rtfm"]):
            await interaction.response.autocomplete([])
            await build_lookup_table(self.bot.session, "python")
            return []

        if not current:
            return [
                app_commands.Choice(name=m, value=m)
                for m in self.bot.cache["rtfm"]["python"][:25]
            ]

        assert interaction.command is not None
        key = getattr(interaction.namespace, "key", "python")
        if not key in self.bot.cache["rtfm"]:
            self.bot.cache["rtfm"][key] = await build_lookup_table(
                self.bot.session, key
            )

        items = self.bot.cache["rtfm"][key]

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
    @choices(key=[Choice(name=m.value.name, value=m.name) for m in Manuals])
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
                the documentation key (python, discord, ...). 
                Defaults to ``python``

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
            default = "python"
            if key is None:
                key = default
            else:
                try:
                    lowered = key.lower()
                    key = Manuals[lowered].name
                except KeyError:
                    if entity is None:
                        entity = key
                        key = default
                    else:
                        return await ctx.send(
                            "Wrong key... know what you do!", ephemeral=True
                        )
            await do.command(ctx).__await__(key, entity)

        except:
            if ctx.testing:
                raise Testing
            raise

    @hybrid_command(name="rtfms")
    @setlocale()
    @is_owner()
    @locale_doc
    async def rtfms(self, ctx: ShakeContext, member: Greedy[Member] = None):
        _(
            """View the members stats of the rtfm command.
            
            Parameters
            -----------
            member: Greedy[Member]
                the members you want to get the stats from"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else rtfm

        try:
            await do.command(ctx=ctx).stats(member=member)

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(rtfm_extension(bot))


#
############
