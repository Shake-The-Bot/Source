############
#
from importlib import reload
from typing import Optional, Union

from discord import PartialEmoji, TextChannel
from discord.app_commands import Choice, choices
from discord.ext.commands import guild_only, hybrid_group

from Classes import (
    ShakeBot,
    ShakeContext,
    Testing,
    _,
    extras,
    has_permissions,
    locale_doc,
    setlocale,
)

from ..community import Community
from . import counting, testing


########
#
class counting_extension(Community):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot, cog=self)
        try:
            reload(counting)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{INPUT SYMBOL FOR NUMBERS}")

    @hybrid_group(name="counting")
    @guild_only()
    @setlocale()
    @locale_doc
    async def counting(self, ctx: ShakeContext):
        _("""Start with 1 and never stop counting again!""")
        ...

    @counting.command(name="setup")
    @guild_only()
    @has_permissions(testing=True, administrator=True)
    @extras(permissions=True)
    @setlocale()
    @locale_doc
    async def setup(
        self,
        ctx: ShakeContext,
        /,
        channel: Optional[TextChannel] = None,
        goal: Optional[int] = None,
        only_numbers: Optional[bool] = True,
        react: Optional[bool] = True,
    ):
        _(
            """Setup the whole Counting game in seconds
            Get more information about the counting game with {command}"""
        ).format(command="`/counting info`")

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else counting

        try:
            await do.command(ctx=ctx).setup(
                channel=channel, goal=goal, numbers=only_numbers, react=react
            )

        except:
            if ctx.testing:
                raise Testing
            raise

    @counting.command(name="score")
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

        do = testing if ctx.testing else counting

        try:
            await do.command(ctx=ctx).score(type=type)

        except:
            if ctx.testing:
                raise Testing
            raise

    @counting.command(name="info")
    @guild_only()
    @setlocale()
    @locale_doc
    async def info(self, ctx: ShakeContext):
        _("""Everything you need to know about the Counting game""")

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else counting

        try:
            await do.command(ctx=ctx).info()

        except:
            if ctx.testing:
                raise Testing
            raise

    @counting.command(name="configure")
    @guild_only()
    @extras(permissions=True)
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def configure(
        self,
        ctx: ShakeContext,
        channel: TextChannel,
        count: Optional[int] = None,
        react: Optional[bool] = None,
    ):
        _("""Change some properties about the Counting game""")

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else counting

        try:
            await do.command(ctx=ctx).configure(
                channel=channel, count=count, react=react
            )

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(counting_extension(bot))


#
############
