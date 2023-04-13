############
#
from Classes import ShakeBot, ShakeContext, ShakeEmbed
from contextlib import suppress
from typing import Any
from Exts.Functions.Scheduled.freegames.stores.models import ProductDataType
from Exts.Functions.Scheduled.freegames.freegames import freegames_event
from Classes.i18n import _, current_locale
from discord import PermissionOverwrite, Forbidden, HTTPException
########
#
class freegames_command():
    def __init__(self, ctx, stores: Any):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.stores: Any = stores

    async def __await__(self):
        return None

    async def set_locale(self):
        locale = await self.bot.locale.get_guild_locale(self.ctx.guild.id) or 'en-US'
        current_locale.set(locale)
        return locale

    async def setup(self):
        await self.ctx.defer()
        locale = await self.set_locale()

        """ creating """
        with suppress(Forbidden, HTTPException):
            category = await self.ctx.guild.create_category(
                name=_("freegames category"), overwrites={
                    self.ctx.guild.default_role: PermissionOverwrite(view_channel=True, send_messages=False,read_messages=True, read_message_history=True), 
                    self.bot.user: PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True, external_emojis=True)
            })

            channel = await self.ctx.guild.create_text_channel(
                name=_("︱aboveme"), category=category)

            game = ProductDataType(
                id='test', title=_('Preview Game'), 
                description=_('This is a preview of this function. It brings a lot with it for example a overview of the prizes and an instant link to the launcher!'),
                price=10000, currency='$', price_with_currency='$100.00', thumbnail=self.bot.user.avatar.url, image=None, url='ttps://top.gg/bot/778938275397632021/vote',
                publisher='Shake Developement', reviews=None, store='Preview Store', start=None, end=None
            )
            embed = freegames_event(bot=self.bot, guild=self.ctx.guild).embed_from_product(game=game)
            await channel.send(embed)
            
        await self.bot.config_pool.execute(
            """INSERT INTO freegames (channel_id, guild_id, stores) VALUES ($1, $2, $3)""", 
            channel.id, self.ctx.guild.id, self.stores
        )

        embed = ShakeEmbed.default(self.ctx, description = _("{emoji} {prefix} **Setup completed**. {channel} now will be used to announce newly free games from the selected stores!".format(
                emoji=self.bot.emojis.hook, prefix=self.bot.emojis.prefix, channel=channel.mention
        )))
        return await self.ctx.smart_reply(embed=embed)