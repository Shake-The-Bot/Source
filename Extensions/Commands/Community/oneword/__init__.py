############
#
from importlib import reload
from typing import Optional, Union

from discord import PartialEmoji, TextChannel
from discord.app_commands import Choice, choices
from discord.ext.commands import guild_only, has_permissions, hybrid_group

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..community import Community
from . import oneword, testing


########
#
class oneword_extension(Community):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot, cog=self)
        try:
            reload(oneword)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{INPUT SYMBOL FOR NUMBERS}")

    @hybrid_group(name="oneword")
    @guild_only()
    @setlocale()
    @locale_doc
    async def oneword(self, ctx: ShakeContext):
        _("""Create some funny sentances with the help of other users!""")
        ...

    @oneword.command(name="setup")
    @guild_only()
    @has_permissions(administrator=True)
    @extras(permissions=True)
    @setlocale()
    @locale_doc
    async def setup(
        self,
        ctx: ShakeContext,
        /,
    ):
        _(
            """Setup the whole OneWord game in seconds
            Get more information about the OneWord game with {command}"""
        ).format(command="`/oneword info`")

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else oneword

        try:
            await do.command(ctx=ctx).setup()

        except:
            if ctx.testing:
                raise Testing
            raise

    @oneword.command(name="info")
    @guild_only()
    @setlocale()
    @locale_doc
    async def info(self, ctx: ShakeContext):
        _("""Everything you need to know about the OneWord game""")

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else oneword

        try:
            await do.command(ctx=ctx).info()

        except:
            if ctx.testing:
                raise Testing
            raise

    @oneword.command(name="score")
    @choices(
        type=[
            Choice(name="Servers", value="servers"),
            Choice(name="Users", value="users"),
        ]
    )
    @guild_only()
    @setlocale()
    @locale_doc
    async def score(self, ctx: ShakeContext, type: Optional[str] = "Servers"):
        _("""View the top Counting users and servers""")

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else oneword

        try:
            await do.command(ctx=ctx).score(type=type)

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(oneword_extension(bot))


#
############
