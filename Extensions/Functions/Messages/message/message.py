from typing import Optional, Tuple

from discord import Guild, Message, TextChannel
from discord.ext.commands import CooldownMapping

from Classes import ShakeBot, ShakeEmbed, _, cleanup

SystemType = Tuple[Optional[ShakeEmbed], bool, bool]
############
#


class Event:
    bot: ShakeBot
    guild: Guild
    channel: TextChannel
    message: Message
    spam_control: CooldownMapping

    def __init__(self, message: Message, bot: ShakeBot):
        self.bot = bot
        self.author = message.author
        self.guild = message.guild
        self.channel = message.channel
        self.content = message.content
        self.message = message

    async def __await__(self):
        ctx = await self.bot.get_context(self.message)

        if ctx and ctx.valid and ctx.command:
            return

        if self.bot.user.mentioned_in(self.message) and not bool(
            self.message.attachments
        ):
            content = cleanup(self.content.strip())
            if len(content.split()) == 1:
                content = content.replace(self.bot.user.mention, "", 1)
                if len(content) == 0:
                    message = _("Hey {user}! My prefix is / or {mention}").format(
                        user=self.author.mention,
                        mention=self.bot.user.mention,
                    )
                    try:
                        await self.message.reply(message)
                    except:
                        await self.channel.send(message)
                    finally:
                        return
        return


#
############
