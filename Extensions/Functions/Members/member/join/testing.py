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
    async def greet(self):
        async with ctx.pool.acquire() as connection:
            # Check the database for the guild's welcome channel if not then ignore
            query = "SELECT channel_id FROM welcome WHERE guild_id = $1"
            if not (channel := await connection.fetch(query, self.guild.id)):
                return
            else:
                # Get everything from the database (using guild_id)
                query = "SELECT * FROM welcome WHERE guild_id = $1"
                data = await connection.fetchrow(query, self.guild.id)
                channel_id = data["channel_id"]
                message = data["message"]
                is_embed = data["is_embed"]
                # Get the channel object
                channel = self.bot.get_channel(channel_id)
                # If the channel is not found then ignore
                if not channel:
                    return
                # If the channel is found then send the message
                else:
                    # If the message is embed then send embed
                    if is_embed:
                        embed = ShakeEmbed()
                        embed.description = message
                        await channel.send(embed=embed)
                    # If the message is not embed then send normal message
                    else:
                        await channel.send(message)
                        

    async def __await__(self):
        # if gpool.captcha
        #     if not await self.captcha():
        #         await self.member.guild.kick(self.member, reason="Captcha Failed")
        return


#
############
