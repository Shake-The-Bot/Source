from contextlib import suppress
from re import compile, escape

from discord import (
    ButtonStyle,
    HTTPException,
    NotFound,
    PartialEmoji,
    User,
    Webhook,
    ui,
)
from topgg.types import BotVoteData

from Classes import ShakeBot, _

############
#


class Link(ui.View):
    def __init__(self, link):
        super().__init__(timeout=None)
        self.add_item(
            ui.Button(
                style=ButtonStyle.blurple,
                emoji=PartialEmoji(name="arrow", id=1093146865706479756),
                label="You can vote for Shake every 12h!",
                url=link,
            )
        )


class Event:
    def __init__(self, bot: ShakeBot, data: dict):
        self.bot: ShakeBot = bot
        self.data: BotVoteData = data

    async def __await__(self):
        """This functions is called whenever someone votes for the bot on Top.gg"""

        user: User = await self.bot.get_user_global(user_id=int(self.data.user))

        rep = dict(
            (escape(k), "") for k in ["discord", "Discord", "everyone", "Everyone"]
        )

        user_name = compile("|".join(rep.keys())).sub(
            lambda m: rep[escape(m.group(0))], str(user)
        )
        webhooks = list(
            filter(
                lambda item: item is not None,
                [
                    Webhook.from_url(webhook.link, client=self.bot)
                    for webhook in self.bot.config.bot.webhooks
                    if webhook.type == "votes"
                ],
            )
        )
        for webhook in webhooks:
            try:
                await webhook.edit(
                    name=user_name, avatar=await user.avatar.read(), reason="Logs"
                )
            except (HTTPException, NotFound, ValueError, AttributeError):
                continue
            else:
                with suppress(HTTPException, NotFound):
                    await webhook.send(
                        content="{emoji} `{name}` has voted for me!.".format(
                            emoji=PartialEmoji(
                                animated=True, name="blobjoin", id=1058033663675207820
                            ),
                            name=user_name,
                        ),
                        view=Link(self.bot.config.other.topgg.vote),
                    )


#
############
