############
#
from discord import Forbidden, NotFound, HTTPException, Interaction
from traceback import format_exception
from Classes.exceptions import *
from typing import Union
from Classes.i18n import _
from contextlib import suppress
from discord.ext.commands import errors
from Classes.useful import levenshtein
from Classes import ShakeBot, ShakeContext, ShakeEmbed
########
#
class command_error_event():
    def __init__(self, ctx: Union[ShakeContext, Interaction], error):
        self.bot: ShakeBot = ctx.bot if isinstance(ctx, ShakeContext) else ctx.client
        self.ctx: Union[ShakeContext, Interaction] = ctx
        self.error: errors.CommandError = error

    async def __await__(self):
        embed = ShakeEmbed.to_error()
        original = getattr(self.error, "original", self.error)
        raisable: bool = False

        if isinstance(original, errors.CommandNotFound):
            await self.command_not_found(self.ctx, embed)
            return

        elif isinstance(original, (ShakeMissingPermissions,)):
            embed.description =  f'{self.bot.emojis.cross} {self.bot.emojis.prefix} ' + '**'+(original.message or _("I am missing `{permissions}` permission(s) to run this command.").format(permissions=', '.join(original.missing_permissions))) +'**'


        elif isinstance(original, (errors.MissingRequiredArgument, errors.MissingRequiredAttachment, errors.TooManyArguments, BadArgument, errors.BadUnionArgument, errors.BadLiteralArgument, errors.UserInputError)):
            embed.description = f'{self.bot.emojis.cross} {self.bot.emojis.prefix} **{original.message or _("You did something wrong with the arguments, try !help")}**'

        elif isinstance(original, (GuildNotFound,)):
            embed.description =  f'{self.bot.emojis.cross} {self.bot.emojis.prefix} ' + '**'+(original.message or _("I cannot see the server `{argument}` because it does not exist or I am not a member of it.").format(argument=original.argument)) +'**'

        elif isinstance(original, errors.CommandInvokeError):
            if isinstance(original, Forbidden):
                return # TODO

            elif isinstance(original, NotFound):
                embed.description = f'{self.bot.emojis.cross} {self.bot.emojis.prefix} **{_(f"This type of entity does not exist: {original.text}")}**'

            elif isinstance(original, HTTPException):
                raisable = True
                embed.description = f'{self.bot.emojis.cross} {self.bot.emojis.prefix} **{_("Somehow, an unexpected error occurred. Try again later?")}**'

        elif isinstance(original, NothingHereYet):
            raisable = True
            embed.description = f'{self.bot.emojis.cross} {self.bot.emojis.prefix} **{_("Someone messed up in the implementation of this function...")}**'

        elif isinstance(original, errors.CommandOnCooldown):
            embed.description = f'{self.bot.emojis.cross} {self.bot.emojis.prefix} **{_("You can use this command in {0:.0f} seconds.").format(original.retry_after)}**'

        elif isinstance(original, errors.NotOwner):
            embed.description = f'{self.bot.emojis.cross} {self.bot.emojis.prefix} **{_("Only the bot owner can run the command `{command}`.").format(command=self.ctx.command)}**'

        elif isinstance(original, errors.MissingPermissions):
            embed.description = f'{self.bot.emojis.cross} {self.bot.emojis.prefix} **{_("You are missing `{permission}` permission(s) to run this command.").format(permission=", ".join(original.missing_permissions))}**'

        else:  
            raisable = True
            embed.description = f'{self.bot.emojis.cross} {self.bot.emojis.prefix} **{_("Something wrong happened")}**'
        await self.send(embed, raisable)
        return

    async def send(self, embed: ShakeEmbed, raisable: bool = False, **kwargs: Any):
        if raisable:
            dumped = await self.bot.dump(f"{''.join(format_exception(self.error.__class__, self.error, self.error.__traceback__))}")
            self.bot.log.warning(f"{self.ctx.guild.id} > {(self.ctx.author if isinstance(self.ctx, ShakeContext) else self.ctx.user).id} > {self.ctx.command}: {dumped} ({self.error.__class__.__name__})")
        try:
            if isinstance(self.ctx, Interaction):
                if self.ctx.response.is_done():
                    await self.ctx.followup.send(embed=embed, ephemeral=True)
                else:
                    await self.ctx.response.send_message(embed=embed, ephemeral=True)
            else:
                await self.ctx.smart_reply(embed=embed, ephemeral=True, error=True, **kwargs)
            
            if raisable:
                embed.description = f'{self.bot.emojis.hook} {self.bot.emojis.prefix} **{_("The {} error was reported to the Shake-Team!").format(self.error.__class__.__name__)}**'
                if isinstance(self.ctx, Interaction):
                    await self.ctx.followup.send(embed=embed, ephemeral=True)
                else:
                    await self.ctx.smart_reply(embed=embed, ephemeral=True, error=True, **kwargs)
        except:
            raise

    async def command_not_found(self, ctx: ShakeContext, embed):
        invoked = ctx.message.content.replace(ctx.prefix, '', 1).split()[0]
        closest = (99999, None)
        for command in self.bot.commands:
            extras = getattr(command.callback, "extras", {})
            if not (
                not extras.get("owner", False) == await ctx.bot.is_owner(ctx.author)
            ) and not extras.get("hidden", False):
                continue
            distance = levenshtein(invoked, command.name, ratio_calc=True)
            if not distance:
                continue
            if distance < closest[0]:
                closest = (distance, command.qualified_name)
        embed.description=_(
            "No command named `{invoked_command}` found. Use \"{prefix}help\" for help."
        ).format(invoked_command=invoked, prefix=ctx.prefix)
        if closest[0] < 10 and closest[1] is not None:
            embed.description = _(
                """Nothing named `{invoked_command}` found. Did you mean **/{closest_1}** ?"""
            ).format(invoked_command=invoked, prefix=ctx.prefix, closest_1=closest[1])
        await self.send(embed, error=True)
        return


#
############
