############
#
from Classes import ShakeBot, ShakeContext, ShakeEmbed
from contextlib import suppress
from asyncpg import Pool
from Classes.i18n import _, current
from discord import PermissionOverwrite, Forbidden, HTTPException
########
#
class command():
    def __init__(self, ctx, **kwargs):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.kwargs = kwargs

    async def __await__(self):
        return None

    async def set_locale(self):
        locale = await self.bot.locale.get_guild_locale(self.ctx.guild.id) or 'en-US'
        current.set(locale)
        return locale
        
    async def setup(self):
        await self.ctx.defer()
        locale = await self.set_locale()
        db: Pool = await self.bot.get_pool(_id=self.ctx.guild.id)

        """ creating """
        with suppress(Forbidden, HTTPException):
            category = await self.ctx.guild.create_category(
                name=_("oneword category"), overwrites={
                    self.ctx.guild.default_role: PermissionOverwrite(
                        view_channel=True, send_messages=True, speak=True, 
                        use_voice_activation=True, stream=True, read_messages=True, 
                        read_message_history=True, connect=True
                    )}) 
            channel = await self.ctx.guild.create_text_channel(
                name=_("︱oneword"), category=category)
            message = await channel.send(_("I"))
            await message.add_reaction('☑️')
        
        if not category or not channel: 
            return await self.ctx.smart_reply("Something went wrong") # TODO: if no permissions

        await self.bot.config_pool.execute(
            """INSERT INTO oneword (channel_id, guild_id, turn) VALUES ($1, $2, $3)""", 
            channel.id, self.ctx.guild.id, True
        )
        embed = ShakeEmbed.default(self.ctx, description = _("{emoji} {prefix} **Setup completed**. {channel} can now be used to play oneword on this Discord server!".format(
            emoji=self.bot.emojis.hook, prefix=self.bot.emojis.prefix, channel=channel.mention)
        ))
        return await self.ctx.smart_reply(embed=embed)