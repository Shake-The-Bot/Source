############
#
from importlib import reload
from random import choice
from typing import Optional, Union

from discord import Member, PartialEmoji, User
from discord.ext.commands import Cog, guild_only, hybrid_command
from discord.ext.commands.converter import MemberConverter, MemberNotFound

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from ..information import Information
from . import testing, userinfo


########
#
class userinfo_extension(Information):
    def __init__(self, bot) -> None:
        super().__init__(bot=bot)
        try:
            reload(userinfo)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="ℹ️")

    @hybrid_command(name="userinfo", aliases=["ui"])
    @guild_only()
    @setlocale()
    @locale_doc
    async def userinfo(
        self, ctx: ShakeContext, user: Optional[Union[User, Member]] = None
    ):
        _(
            """Get information about you or a specified user.
            
            Parameters
            -----------
            user: Optional[Union[Member, User]]
                @mention, ID or name of the user you want to get information about."""
        )
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical(
                    "Could not load {name}, will fallback ({type})".format(
                        name=testing.__file__, type=e.__class__.__name__
                    )
                )
                ctx.testing = False

        do = testing if ctx.testing else userinfo

        member = None
        if not user is None:
            try:
                member = await MemberConverter().convert(ctx=ctx, argument=str(user))
            except MemberNotFound:
                pass

        fallback = None
        if user is None:
            user = await self.bot.fetch_user(ctx.author.id)
            try:
                member = await MemberConverter().convert(
                    ctx=ctx, argument=str(ctx.author)
                )
            except MemberNotFound:
                pass

        elif not user is None:
            if isinstance(user, Member):
                user = await self.bot.fetch_user(user.id)
                member = user

            if isinstance(user, User):
                user = await self.bot.fetch_user(user.id)

                try:
                    member = await MemberConverter().convert(
                        ctx=ctx, argument=str(user)
                    )
                except MemberNotFound:
                    if bool(user.mutual_guilds):
                        guild = choice(user.mutual_guilds)
                        fallback = guild.get_member(user.id)
                    else:
                        pass

            else:
                self.bot.log.debug(
                    "userinfo command passed unknown <user> arg: {}".format(user)
                )
                member = None

        try:
            await do.command(
                ctx=ctx, user=user or ctx.author, member=member, fallback=fallback
            ).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(userinfo_extension(bot))


#
############
