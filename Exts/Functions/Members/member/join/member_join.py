############
#
from discord import Member, Guild, Forbidden, HTTPException
from Classes import ShakeBot, ShakeEmbed
from asyncpg import Pool
from logging import getLogger
from inspect import cleandoc
from Classes import _
from contextlib import suppress
from Classes.useful import captcha
from asyncio import TimeoutError
########
#
class Event():
    def __init__(self, member: Member, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.member: Member = member
        self.guild: Guild = member.guild
        
    async def await_captcha(self):
        file, password = await captcha(self.bot)
        embed = ShakeEmbed(title=_("Please send the captcha code here"), description=cleandoc(_(
            """Hello! You are required to complete a captcha before entering the server.
            __**NOTE:**__ This is **not** Case Sensitive.

            **Why?**
            This is to protect the server against
            targeted attacks using automated user accounts.
            
            **Your Captcha:**"""
        )))
        embed.set_author(name=_("Welcome to {guild_name}").format(guild_name=self.member.guild.name), icon_url=self.member.avatar)
        embed.set_image(url=f"attachment://{file.filename}")
        with suppress(Forbidden, HTTPException):
            await self.member.send(embed=embed, file=file)

            try:
                msg = await self.bot.wait_for('message', timeout=120.0, check=lambda m: m.author == self.member)
            except TimeoutError:
                await self.member.guild.kick(self.member, reason="Captcha Failed")
                return False
            if not msg.content.lower() == password.lower():            
                await self.member.guild.kick(self.member, reason="Captcha Failed")
                return False
            embed = ShakeEmbed(description=_(
                    "{emoji} {prefix} **Thank you! You have been verified in guild __`{guild_name}`__**"
                ).format(guild_name=self.member.guild, emoji=self.bot.emojis.hook, prefix=self.bot.emojis.prefix
            ))
            await self.member.send(embed=embed)
            return True


            
    async def __await__(self):
        self.db: Pool = await self.bot.get_pool(_id=self.member.guild.id)
        self.config: Pool = self.bot.config_pool
        if bool(await self.config.fetch("SELECT captcha FROM welcome WHERE guild_id = $1 AND turn = $2", self.member.guild.id, True) or None):
            _captcha = await self.await_captcha()
        return
#
############