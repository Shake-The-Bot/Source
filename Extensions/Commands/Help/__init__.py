############
#
from importlib import reload
from typing import Optional

from discord.app_commands import Choice, choices
from discord.ext.commands import Cog, guild_only, hybrid_command

from Classes import (
    Categorys,
    Format,
    ShakeBot,
    ShakeContext,
    Testing,
    _,
    locale_doc,
    setlocale,
)

from . import help, testing

########
#


class help_extension(Cog):
    def __init__(self, bot) -> None:
        self.bot: ShakeBot = bot
        try:
            reload(help)
        except:
            pass

    @hybrid_command(name="help")
    @guild_only()
    @setlocale()
    @choices(
        category=[
            Choice(name="Community", value="Community"),
            Choice(name="Gimmicks", value="Gimmicks"),
            Choice(name="Information", value="Information"),
            Choice(name="Moderation", value="Moderation"),
            Choice(name="Other", value="Other"),
        ]
    )
    @locale_doc
    async def help(
        self,
        ctx: ShakeContext,
        category: Optional[str] = None,
        *,
        command: Optional[str] = None,
    ):
        _(
            """Shows all Shake bot commands and provides helpful links
        
            Parameters
            -----------
            category: Optional[str]
                the name of a category you want information about

            command: Optional[str]
                the name of a command you want information about
            """
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else help

        try:
            if not category is None:
                try:
                    lowered = category.lower()
                    category = Categorys[lowered].value
                except KeyError:
                    if command is None:
                        command = category
                    else:
                        command = " ".join(category, command)
                    category = None

            await do.command(
                ctx=ctx,
                category=category,
                command=command,
            ).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise

        return


async def setup(bot: ShakeBot):
    bot.remove_command("help")
    # bot.help_command = HelpPaginatedCommand()
    await bot.add_cog(help_extension(bot))


#
############
