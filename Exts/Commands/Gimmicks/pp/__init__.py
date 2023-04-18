############
#
from discord import PartialEmoji, Member
from importlib import reload
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, Testing
from . import pp, testing
from discord.ext.commands import Cog, guild_only, Greedy, hybrid_command
########
#
class pp_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{VIDEO GAME}')

    def category(self) -> str: 
        return "gimmicks"
    
    @hybrid_command(name="pp")
    @guild_only()
    @setlocale()
    @locale_doc
    async def pp(self, ctx: ShakeContext, member: Greedy[Member] = None):
        _(
            """Reveal the length of a user's pp

            With this command you can find out, using a very clever and definitely not random generator,
            how long the pp of a selected user is.
            
            __Please note__: If you don't specify a user, I might reveal your pp as well.

            Parameters
            -----------
            member: Greedy[Member]
                the member to ban"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False

        do = testing if ctx.testing else pp
        try:    
            await do.command(ctx=ctx, member=member or [ctx.author]).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

########
#
async def setup(bot: ShakeBot): 
    await bot.add_cog(pp_extension(bot))
#
############