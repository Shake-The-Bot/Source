############
#
from importlib import reload
from typing import Optional

from discord.ext.commands import Cog, guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale
from Classes.useful import Categorys

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
    @locale_doc
    async def help(
        self,
        ctx: ShakeContext,
        category: Optional[Categorys] = None,
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
            await do.command(ctx=ctx, category=category, command=command).__await__()

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
