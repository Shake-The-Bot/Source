############
#
from difflib import get_close_matches
from traceback import format_exception
from typing import List, Optional, Union

from discord import Forbidden, HTTPException, Interaction, NotFound
from discord.ext.commands import Command, errors

from Classes import ShakeBot, ShakeContext, ShakeEmbed, Slash, _
from Classes.exceptions import *


########
#
class Event:
    def __init__(self, ctx: Union[ShakeContext, Interaction], error):
        self.bot: ShakeBot = ctx.bot if isinstance(ctx, ShakeContext) else ctx.client
        self.ctx: Union[ShakeContext, Interaction] = ctx
        self.error: errors.CommandError = error

    async def __await__(self):
        if not self.ctx in self.bot.cache["context"]:
            self.bot.cache["context"].append(self.ctx)
        original = getattr(self.error, "original", self.error)
        raisable: bool = False

        self.testing = isinstance(original, Testing)

        if isinstance(original, errors.CommandNotFound):
            await self.command_not_found(self.ctx)
            return

        elif isinstance(original, (ShakeMissingPermissions,)):
            description = original.message or _(
                "I am missing [`{permissions}`](https://support.discord.com/hc/en-us/articles/206029707) permission(s) to run this command."
            ).format(permissions=", ".join(original.missing_permissions))

        if isinstance(original, (errors.BadArgument)):
            description = getattr(original, "message", None) or _(
                "You typed in some bad arguments, try !help"
            )

        elif isinstance(
            original,
            (
                errors.MissingRequiredArgument,
                errors.MissingRequiredAttachment,
                errors.TooManyArguments,
                errors.BadUnionArgument,
                errors.BadLiteralArgument,
                errors.UserInputError,
            ),
        ):
            description = getattr(original, "message", None) or _(
                "You did something wrong with the arguments, try !help"
            )

        elif isinstance(original, (GuildNotFound,)):
            description = original.message or _(
                "I cannot see the server `{argument}` because it does not exist or I am not a member of it."
            ).format(argument=original.argument)

        elif isinstance(original, errors.CommandInvokeError):
            if isinstance(original, Forbidden):
                return  # TODO

            elif isinstance(original, NotFound):
                description = _(f"This type of entity does not exist: {original.text}")

            elif isinstance(original, HTTPException):
                raisable = True
                description = _(
                    "Somehow, an unexpected error occurred. Try again later?"
                )

        elif isinstance(original, NothingHereYet):
            raisable = True
            description = _(
                "Someone messed up in the implementation of this function..."
            )

        elif isinstance(original, errors.CommandOnCooldown):
            description = _("You can use this command in {0:.0f} seconds.").format(
                original.retry_after
            )

        elif isinstance(original, errors.NotOwner):
            description = _(
                "Only the bot owner can run the command `{command}`."
            ).format(command=self.ctx.command)

        elif isinstance(original, errors.MissingPermissions):
            description = _(
                "You are missing `{permission}` permission(s) to run this command."
            ).format(permission=", ".join(original.missing_permissions))

        else:
            raisable = True
            description = _("Something wrong happened")

        await self.send(description, raisable)
        return

    async def command_not_found(self, ctx: ShakeContext):
        invoked = ctx.invoked_with

        commands = dict()
        for command in self.bot.commands:
            extras = getattr(command.callback, "extras", {})
            allowed = (owner := await ctx.bot.is_owner(ctx.author)) or extras.get(
                "owner", False
            ) == owner
            hidden = extras.get("hidden", False)
            if allowed and not hidden:
                commands[command.name] = command
        matches: Optional[List[Command]] = get_close_matches(
            invoked, list(commands.keys())
        )
        help = await Slash(self.bot).__await__("help")
        description = _(
            "No command named `{invoked}` found. Use {help} for help."
        ).format(invoked=invoked, help=help.app_command.mention)

        if bool(matches):
            cmd = await Slash(self.bot).__await__(commands[matches[0]])
            description = _(
                """Nothing named `{invoked}` found. Did you mean {closest}?"""
            ).format(
                invoked=invoked,
                closest=cmd.app_command.mention
                if hasattr(cmd, "app_command")
                else ctx.prefix + cmd.command.name,
            )

        await self.send(description)
        return

    async def send(self, description, raisable: bool = False):
        if raisable:
            try:
                dumped = await self.bot.dump(
                    f"{''.join(format_exception(self.error.__class__, self.error, self.error.__traceback__))}"
                )
            except:
                print(
                    "".join(
                        format_exception(
                            self.error.__class__, self.error, self.error.__traceback__
                        )
                    )
                )
            if not self.testing:
                self.bot.log.warning(
                    f"{self.ctx.guild.id} > {(self.ctx.author if isinstance(self.ctx, ShakeContext) else self.ctx.user).id} > {self.ctx.command}: {dumped} ({self.error.__class__.__name__})"
                )

        embed = (
            ShakeEmbed.to_success(self.ctx, description=dumped)
            if raisable and self.testing
            else ShakeEmbed.to_error(self.ctx, description=description)
        )

        if isinstance(self.ctx, Interaction):
            if self.ctx.response.is_done():
                await self.ctx.followup.send(embed=embed, ephemeral=True)
            else:
                await self.ctx.response.send_message(embed=embed, ephemeral=True)
        else:
            await self.ctx.send(embed=embed, ephemeral=True)

        if raisable and not self.testing:
            embed = ShakeEmbed.to_success(
                self.ctx,
                description=_(
                    "The {type} {error} was reported to the Shake-Team!"
                ).format(
                    type=self.error.__class__.__name__,
                    error=""
                    if self.error.__class__.__name__.lower().endswith("error")
                    else _("error"),
                ),
            )
            if isinstance(self.ctx, Interaction):
                await self.ctx.followup.send(embed=embed, ephemeral=True)
            else:
                await self.ctx.send(embed=embed, ephemeral=True)


#
############
