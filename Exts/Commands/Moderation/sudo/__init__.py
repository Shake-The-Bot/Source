############
#
from discord import PartialEmoji
from importlib import reload
from typing import Optional, Union
from discord import TextChannel, Member, User
from . import sudo, testing
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, extras, Testing
from discord.ext.commands import Cog, hybrid_command, has_permissions, guild_only
########
#
class sudo_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot
        try:
            reload(sudo)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{WASTEBASKET}')

    def category(self) -> str: 
        return "moderation"


    @hybrid_command(name="sudo")
    @extras(permissions=True)
    @has_permissions(administrator=True)
    @guild_only()
    @setlocale(guild=True)
    @locale_doc
    async def sudo(self, ctx: ShakeContext, channel: Optional[TextChannel], user: Union[Member, User], command: str, *, arguments: Optional[str] = None):
        _(
            """execute commands with the rights of another user

            You can specify who executes this command in which text channel"

            Parameters
            -----------
            channel: Optional[TextChannel]
                the channel

            user: Union[Member, User]
                the user

            command: str
                the command

            arguments: Optional[str]
                the arguments
            """
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.__testing = False
        do = testing if ctx.testing else sudo

        try:    
            await do.command(ctx=ctx, channel=channel, user=user, command=command, args=arguments).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot):
    await bot.add_cog(sudo_extension(bot))
#
############