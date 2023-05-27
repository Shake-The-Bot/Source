############
#
from Classes import ShakeBot, ShakeContext, ShakeEmbed
from contextlib import suppress
from asyncpg import Pool
from Classes.i18n import _, current
from discord import Forbidden, PermissionOverwrite, ButtonStyle, ui, PartialEmoji, Interaction, HTTPException
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
        await self.ctx.defer(ephemeral=True)
        locale = await self.set_locale()
        db: Pool = await self.bot.get_pool(_id=self.ctx.guild.id)

        """ creating """
        try:
            category = await self.ctx.guild.create_category(
                name=_("tempvoice category"), overwrites={
                    self.ctx.guild.default_role: PermissionOverwrite(
                        view_channel=True, send_messages=False, speak=False, use_voice_activation=False,
                        stream=False, read_messages=False, read_message_history=False, 
                        connect=True # if self.kwargs.pop('locked', False) else False
                  # self.bot.user: PermissionOverwrite()})
            )})
            creator = await self.ctx.guild.create_voice_channel(
                name=_("︱Creator Channel"), bitrate=96000, category=category, overwrites={
                    self.ctx.guild.default_role: PermissionOverwrite(
                        view_channel=True, connect=True, speak=False),
                    self.bot.user: PermissionOverwrite(
                        view_channel=True, manage_channels=True, connect=True,
                        move_members=True
                    )})
            interface = await self.ctx.guild.create_text_channel(
                name=_("︱interface"), category=category, overwrites={
                    self.ctx.guild.default_role: PermissionOverwrite(
                        view_channel=True, send_messages=False,
                        read_messages=True, read_message_history=True),
                    self.bot.user: PermissionOverwrite(
                        view_channel=True, manage_channels=True, send_messages=True, use_external_emojis=True
                    )
            })
            overwrites = interface.overwrites_for(self.bot.user)
            image = await self.bot.user.avatar.read()
            webhook = await interface.create_webhook(
                name="TempVoice", avatar=image
                )
        except Forbidden:
            await self.ctx.smart_reply("I lack the rights to create/edit channels")
            return
        else:
            """ interface """
            embed = ShakeEmbed.default(self.ctx, title=_("TempVoice Interface"), description= _(
                """{emoji} This interface can be used to edit your temporary channel.
                More options will be available with {command} commands.""").format(
                    emoji=self.bot.emojis.hook, command="/tempvoice"
                ))

            await webhook.send(embed=embed, view=TempvoiceButtonView(self.bot)) #str(webhook.url), 

            """ registration """
            await self.bot.config_pool.execute(
                """INSERT INTO tempvoice (
                    creator_id, guild_id, turn, category_id, webhook_url, prefix, suffix, locked, user_limit
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""", 
                creator.id, self.ctx.guild.id, True, category.id, webhook.url,
                self.kwargs.pop('prefix', ''), self.kwargs.pop('suffix', ''),
                self.kwargs.pop('locked', False), self.kwargs.pop('user_limit', None),)
            

            """ finishing """
            class Buttons(ui.View):
                def __init__(self, bot: ShakeBot):
                    super().__init__(timeout=None)
                    self.add_item(ui.Button(label=_("Support"), url=bot.config.other.server))

            await self.ctx.smart_reply(
                "{emoji} {__}Setup completed{__}. {channel} can now be used to create temporary channels on this Discord server!"
                .format(emoji=self.bot.emojis.hook, channel=creator.mention, __='**'), view=Buttons(self.bot), ephemeral=True
            )
        return

class TempvoiceButtonView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=0.1)
        self.bot: ShakeBot = bot

    @ui.button(
        emoji=PartialEmoji(name='rename', id=1092153318983335938), 
        style=ButtonStyle.green, row=0, custom_id="tempvoice-rename"
        )
    async def rename(self, interaction: Interaction, button: ui.Button):
        return False
    
    @ui.button(
        emoji=PartialEmoji(name='limit', id=1092156599843426324), 
        style=ButtonStyle.green, row=0, custom_id="tempvoice-limit"
        )
    async def limit(self, interaction: Interaction, button: ui.Button):
        return False
    
    @ui.button(
        emoji=PartialEmoji(name='close', id=1092153376571150387), 
        style=ButtonStyle.green, row=0, custom_id="tempvoice-privacy"
        )
    async def privacy(self, interaction: Interaction, button: ui.Button):
        return False
    
    @ui.button(
        emoji=PartialEmoji(name='transfer', id=1092153397303578644), 
        style=ButtonStyle.green, row=0, custom_id="tempvoice-transfer"
        )
    async def transfer(self, interaction: Interaction, button: ui.Button):
        return False
    
    @ui.button(
        emoji=PartialEmoji(name='unavailable', id=1092157746100584489), 
        style=ButtonStyle.green, row=0, custom_id="tempvoice-region", disabled=True
        )
    async def region(self, interaction: Interaction, button: ui.Button):
        return False
    
    @ui.button(
        emoji=PartialEmoji(name='trust', id=1092156177242132500), 
        style=ButtonStyle.green, row=1, custom_id="tempvoice-trust"
        )
    async def trust(self, interaction: Interaction, button: ui.Button):
        return False
    
    @ui.button(
        emoji=PartialEmoji(name='block', id=1092153437824753764), 
        style=ButtonStyle.green, row=1, custom_id="tempvoice-block"
        )
    async def block(self, interaction: Interaction, button: ui.Button):
        return False
    
    @ui.button(
        emoji=PartialEmoji(name='kick', id=1092153462621483038), 
        style=ButtonStyle.green, row=1, custom_id="tempvoice-kick"
        )
    async def kick(self, interaction: Interaction, button: ui.Button):
        return False
    
    @ui.button(
        emoji=PartialEmoji(name='claim', id=1092153573887987732), 
        style=ButtonStyle.green, row=1, custom_id="tempvoice-claim"
        )
    async def claim(self, interaction: Interaction, button: ui.Button):
        return False
    
    @ui.button(
        emoji=PartialEmoji(name='unavailable', id=1092157746100584489), 
        style=ButtonStyle.green, row=1, custom_id="tempvoice-thread", disabled=True
        )
    async def thread(self, interaction: Interaction, button: ui.Button):
        return False
    
    @ui.button(
        emoji=PartialEmoji(name='untrust', id=1092156175883173938), 
        style=ButtonStyle.green, row=2, custom_id="tempvoice-untrust"
        )
    async def untrust(self, interaction: Interaction, button: ui.Button):
        return False
    
    @ui.button(
        emoji=PartialEmoji(name='unblock', id=1092153625515655207), 
        style=ButtonStyle.green, row=2, custom_id="tempvoice-unblock"
    )
    async def unblock(self, interaction: Interaction, button: ui.Button):
        return False