############
#
from asyncio import TimeoutError
from contextlib import suppress
from inspect import cleandoc

from discord import Forbidden, Guild, HTTPException, Member

from Classes import Format, ShakeBot, ShakeEmbed, _
from Classes.helpful import Captcha


########
#
class Event:
    def __init__(self, member: Member, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.member: Member = member
        self.guild: Guild = member.guild

    async def captcha(self):
        captcha = Captcha(self.bot)
        file = await captcha.create()

        embed = ShakeEmbed()
        embed.set_author(
            name=_("Welcome to {guild}").format(guild=self.member.guild.name),
            icon_url=self.member.avatar,
        )
        embed.title = (_("Please send the captcha code here"),)
        embed.description = (
            cleandoc(
                _(
                    """Hello! You are required to complete a captcha before entering the server.
            NOTE: This is not Case Sensitive.

            Why?
            This is to protect the server against
            targeted attacks using automated user accounts.
            
            Your Captcha:"""
                )
            ),
        )
        embed.set_image(url=f"attachment://{file.filename}")

        with suppress(Forbidden, HTTPException):
            await self.member.send(embed=embed, file=file)

        try:
            msg = await self.bot.wait_for(
                "message", timeout=120.0, check=lambda m: m.author == self.member
            )
        except TimeoutError:
            return False

        if not captcha.proove(msg.content):
            return False

        with suppress(Forbidden, HTTPException):
            embed = ShakeEmbed()
            embed.description = Format.bold(
                _(
                    "{emoji} {prefix} Thank you! You have been verified in guild `{guild}`"
                ).format(
                    guild=self.member.guild,
                    emoji=self.bot.assets.hook,
                    prefix=self.bot.assets.prefix,
                )
            )

            await self.member.send(embed=embed)

        return True

    async def __await__(self):
        # if gpool.captcha
        #     if not await self.captcha():
        #         await self.member.guild.kick(self.member, reason="Captcha Failed")
        return


#
############
