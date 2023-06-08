############
#
from importlib import reload

from discord import Interaction, InteractionType
from Extensions.Functions.Voice.voice_state_update.utils import system

from Classes import ShakeBot, _


########
#
class Event:
    def __init__(self, bot: ShakeBot, interaction: Interaction):
        self.bot: ShakeBot = bot
        self.interaction: Interaction = interaction

    async def __await__(self):
        command = self.interaction.command
        if (
            command is not None
            and self.interaction.type is InteractionType.application_command
            and not command.__class__.__name__.startswith("Hybrid")
        ):
            ctx = await self.bot.get_context(self.interaction)
            ctx.command_failed = self.interaction.command_failed or ctx.command_failed
            await self.register_command(ctx)
        reload(system)
        custom_id = self.interaction.data.get("custom_id", None)
        if not custom_id:
            return False

        tv = system.TempVoice(
            bot=self.bot,
            interface_id=self.interaction.channel_id,
            member_id=self.interaction.user.id,
            guild_id=self.interaction.guild_id,
        )
        tempvoice_custom_ids = {
            "tempvoice-rename": "rename",
            "tempvoice-limit": "limit",
            "tempvoice-privacy": "privacy",
            "tempvoice-transfer": "transfer",
            "tempvoice-region": "region",
            "tempvoice-trust": "trust",
            "tempvoice-thread": "claim",
            "tempvoice-untrust": "untrust",
            "tempvoice-unblock": "unblock",
            "tempvoice-block": "block",
            "tempvoice-kick": "kick",
            "tempvoice-claim": "claim",
        }
        if not (function_name := tempvoice_custom_ids.get(custom_id, None)) or not (
            function := getattr(tv, function_name, None)
        ):
            return False

        message = await tv.__await__(self.interaction)
        if message and not function_name == "claim":
            await self.interaction.response.send_message(message, ephemeral=True)
            return False

        await function()
        return True


#
############
