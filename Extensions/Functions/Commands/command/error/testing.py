############
#
from difflib import get_close_matches
from traceback import format_exception
from typing import List, Optional

from discord import Forbidden, HTTPException, Interaction, NotFound
from discord.ext.commands import Command, errors

from Classes import ShakeBot, ShakeContext, ShakeEmbed, Slash, _
from Classes.exceptions import *

arguments = (
    errors.MissingRequiredArgument,
    errors.MissingRequiredAttachment,
    errors.TooManyArguments,
    errors.BadUnionArgument,
    errors.BadLiteralArgument,
    errors.UserInputError,
)


########
#
class Event:
    def __init__(self, ctx: ShakeContext | Interaction, error):
        self.ctx: ShakeContext | Interaction = ctx
        self.error: errors.CommandError = error
        self.raisable: bool = False
        self.original = getattr(self.error, "original", None) or self.error
        if self.error.args:
            self.message = "\n".join(self.error.args)
        else:
            self.message = None
        self.testing = isinstance(self.original, Testing)

    async def __await__(self):
        if isinstance(self.ctx, Interaction):
            if self.ctx.command:
                self.ctx = await ShakeContext.from_interaction(self.ctx)
                self.bot = self.ctx.bot
            else:
                self.bot = self.ctx.client
        else:
            self.bot = self.ctx.bot

        if isinstance(self.ctx, ShakeContext) and not self.ctx.done:
            await self.bot.register_command(self.ctx)

            if not self.ctx in self.bot.cache["context"]:
                self.bot.cache["context"].append(self.ctx)

        if isinstance(self.original, errors.CommandNotFound):
            return await self.command_not_found(self.ctx)

        elif isinstance(self.original, errors.BotMissingPermissions):
            description = self.message or _(
                "I am missing [`{permissions}`](https://support.discord.com/hc/en-us/articles/206029707) permission(s) to run this command."
            ).format(permissions=", ".join(self.original.missing_permissions))

        elif isinstance(self.original, errors.GuildNotFound):
            guild = self.original.argument
            description = _("Either this server does not exist or I am not on it.")

        elif isinstance(self.original, (errors.ChannelNotFound, errors.ThreadNotFound)):
            channel = self.original.argument
            description = _("Either this channel does not exist or I can't see it.")

        elif isinstance(self.original, arguments):
            description = self.message or _(
                "You did something wrong with the arguments, try {command}"
            ).format(command=self.ctx.prefix + "help")

        elif isinstance(self.original, errors.CommandInvokeError):
            if isinstance(self.original, Forbidden):
                return  # TODO

            elif isinstance(self.original, NotFound):
                description = _(
                    f"This type of object does not exist: {self.original.text}"
                )

            elif isinstance(self.original, HTTPException):
                self.raisable = True
                description = _(
                    "Somehow, an unexpected error occurred. Try again later?"
                )

        elif isinstance(self.original, errors.CommandOnCooldown):
            description = _("You can use this command in {retry} seconds.").format(
                retry="{0:.0f}".format(self.original.retry_after)
            )

        elif isinstance(self.original, errors.NotOwner):
            description = _(
                "Only the bot owner can run the command `{command}`."
            ).format(command=self.ctx.command.name)

        elif isinstance(self.original, errors.MissingPermissions):
            description = _(
                "You are missing `{permission}` permission(s) to run this command."
            ).format(permission=", ".join(self.original.missing_permissions))

        elif isinstance(self.original, errors.BadArgument):
            description = self.message or _(
                "You typed in some bad arguments, try {command}"
            ).format(command=self.ctx.prefix + "help")

        else:
            self.raisable = True
            description = _("Something wrong happened")

        await self.send(description)
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
            for match in matches:
                cmd = await Slash(self.bot).__await__(commands[match])
                if cmd and hasattr(cmd.app_command, "mention"):
                    description = _(
                        """Nothing named `{invoked}` found. Did you mean {closest}?"""
                    ).format(invoked=invoked, closest=cmd.app_command.mention)
                    break

        return await self.send(description)

    async def send(self, description):
        if self.raisable:
            try:
                dumped = await self.bot.dump(
                    f"{''.join(format_exception(self.error.__class__, self.error, self.error.__traceback__))}"
                )
            except:
                self.bot.log.warning(
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
            if self.raisable and self.testing
            else ShakeEmbed.to_error(self.ctx, description=description)
        )

        if self.raisable and not self.testing:
            embed.set_footer(text=_("The error was reported to the Shake-Team!"))

        if isinstance(self.ctx, Interaction):
            if self.ctx.response.is_done():
                await self.ctx.followup.send(embed=embed, ephemeral=True)
            else:
                await self.ctx.response.send_message(embed=embed, ephemeral=True)
        else:
            await self.ctx.chat(embed=embed, ephemeral=True)


#
############
