############
#
import contextlib
from contextlib import suppress
from re import compile, escape
from typing import Optional

from discord import Guild, HTTPException, NotFound, PartialEmoji, TextChannel, Webhook

from Classes import ShakeBot, _

########
#


class Event:
    def __init__(
        self, bot: ShakeBot, guild: Guild, channel: Optional[TextChannel] = None
    ):
        self.channel: Optional[TextChannel] = channel
        self.bot: ShakeBot = bot
        self.guild: Guild = guild

    async def __await__(self):
        rep = dict(
            (escape(k), "") for k in ["discord", "Discord", "everyone", "Everyone"]
        )
        guild_name = compile("|".join(rep.keys())).sub(
            lambda m: rep[escape(m.group(0))], self.guild.name
        )
        webhooks = list(
            filter(
                lambda item: item is not None,
                [
                    Webhook.from_url(webhook.link, client=self.bot)
                    for webhook in self.bot.config.bot.webhooks
                    if webhook.type == "servers"
                ],
            )
        )
        for webhook in webhooks:
            try:
                await webhook.edit(
                    name=guild_name, avatar=await self.guild.icon.read(), reason="Logs"
                )
            except (HTTPException, NotFound, ValueError, AttributeError):
                continue
            with suppress(HTTPException, NotFound):
                await webhook.send(
                    "{emoji} Left `{name}`. I'm now in {guilds} guilds (-{users} users).".format(
                        emoji=PartialEmoji(
                            animated=True, name="blobleave", id=1058033660755972219
                        ),
                        name=guild_name,
                        guilds=len(self.bot.guilds),
                        users=self.guild.member_count,
                    )
                )

        # with contextlib.suppress(Exception):
        #     if self.bot.cache['pools'].get(self.guild.id, None):
        #         await db.delete_database(self.guild.id,)


#
############
