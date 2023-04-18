############
#
from discord import PartialEmoji, Member
from importlib import reload
from Classes import ShakeContext, _, locale_doc, Testing, ShakeBot
from . import rtfm, testing
from enum import Enum
from discord import app_commands, Interaction
from discord.ext.commands import Cog, guild_only, hybrid_group, Greedy
########
#

class Keys(Enum):
  # format: name = "value"
  discordpy = "latest"
  python = "python"
  Blue = "blue"

class rtfm_extension(Cog):
    """
    rtfm_cog
    """
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot


    @property
    def display_emoji(self) -> str: 
        return PartialEmoji(name='\N{BOOKS}')


    def category(self) -> str: 
        return "information"
    

    async def rtfm_slash_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        if not hasattr(self.bot, '_rtfm_cache'):
            await interaction.response.autocomplete([])
            await rtfm.build_rtfm_lookup_table()
            return []

        if not current:
            return []

        if len(current) < 3:
            return [app_commands.Choice(name=current, value=current)]

        assert interaction.command is not None
        key = interaction.command.name
        matches = rtfm.finder(current, self.bot._rtfm_cache[key])[:10]
        return [app_commands.Choice(name=m, value=m) for m in matches]


    @hybrid_group(name='rtfm')
    @guild_only()
    @app_commands.autocomplete(entity=rtfm_slash_autocomplete)
    @locale_doc
    async def rtfm(self, ctx: ShakeContext, key: Keys, entity: str) -> None:
        _(
            """View objects from certain documentation.

            RTFM is internet slang for the phrase "read the damn manual"."""
        )

        if ctx.testing:
            reload(testing)
        do = testing if ctx.testing else rtfm

        try:    
            await do.command(ctx, key.value, entity).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise


    @rtfm.command(name="stats")
    @locale_doc
    async def stats(self, ctx: ShakeContext, member: Greedy[Member] = None):
        _(
            """View the members stats of the rtfm command.
            
            Parameters
            -----------
            member: Greedy[Member]
                the members you want to get the stats from"""
        )

        if ctx.testing:
            reload(testing)
        do = testing if ctx.testing else rtfm

        try:    
            await do.command(ctx=ctx, member=member).do_sub()
    
        except:
            if ctx.testing:
                raise Testing
            raise



async def setup(bot: ShakeBot): 
    await bot.add_cog(rtfm_extension(bot))
#
############

