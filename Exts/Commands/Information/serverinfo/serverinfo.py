############
#
from discord import Guild, ContentFilter, PartialEmoji
from Classes.i18n import _
from collections import Counter
from Classes.i18n import _
from typing import  Literal, get_args, Dict
from discord.utils import format_dt
from Classes import ShakeBot, ShakeContext, ShakeEmbed
########
#
ValidStaticFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png']
ValidAssetFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png', 'gif']

ctx_tick = lambda bot: (str(bot.emojis.cross), str(bot.emojis.hook))
########
#

"""
Members: 40475 (41bots)
Region: en-US
Created on: Tuesday, 18 July 2017 00:55


Channel info
Text Channels: 38
Voice Channels: 4
Stages: 1
Forums: 3
Threads: 0
Rules: 1
Announcements: 1
"""

class command():
    def __init__(self, ctx: ShakeContext, guild: Guild):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.guild: Guild = guild

    def information(self,) -> Dict[str, str]:
        information = {
            _("ID")+':': f'`{self.guild.id}`',
            _("Created")+':': f'<t:{int(self.guild.created_at.timestamp())}:R>',
            _("Owner")+':': f'`{self.guild.owner}`'
        }
        if not self.guild.member_count == 1:
            information[_("All Members")+':'] = f'`{self.guild.member_count}`'
            status = Counter(str(member.status) for member in self.guild.members)
            emojis = self.bot.emojis.status
            information[''] = '︱'.join([
                str(emojis.online) +'`'+ str(status['online']) +'`', str(emojis.idle) +'`'+ str(status['idle']) +'`',
                str(emojis.donotdisturb) +'`'+ str(status['dnd']) +'`', str(emojis.offline) +'`'+ str(status['offline']) + '`'
            ])
            
        if bool(bots := len([member for member in self.guild.members if member.bot])):
            information[_("Bots")+':'] = '`'+ str(bots) +'`'

        if len(self.guild.roles) > 1:
            information[_("Roles")+':']= '`'+ str(len([role for role in self.guild.roles])) +'`'

        if bool(self.guild.premium_subscription_count):
            information[_("Boosts")+':'] = _("{count} boosts (Level {tier})").format(
                count=self.guild.premium_subscription_count, subscribers=len(self.guild.premium_subscribers), tier=self.guild.premium_tier
            )

        if bool(len(self.guild.stickers)):
            information[_("Stickers")+':'] = '`'+ str(len(self.guild.stickers)) +'/'+ str(self.guild.sticker_limit) +'`'

        if bool(len(self.guild.emojis)):
            information[_("Emojis")+':'] = '`'+ str(len(self.guild.emojis)) +'/'+ str(self.guild.emoji_limit) +'`'
        return information

    def channelinfo(self,) -> Dict[str, str]:
        information = dict()
        emojis = (self.bot.emojis.hook, self.bot.emojis.cross)
        information[_("Categories")+':'] = '`'+ str((len(self.guild.categories))) +'`'
        information[_("Text Channels")+':'] = '`'+ str(len([channel for channel in self.guild.text_channels if channel.is_news])) +'`'
        information[_("Voice Channels")+':'] = '`'+ str(len(self.guild.voice_channels)) +'`'
        information[_("Stages")+':'] = '`'+ str(len(self.guild.stage_channels)) +'`'
        information[_("Forums")+':'] = '`'+ str(len(self.guild.forums)) +'`'
        information[_("Threads")+':'] = '`'+ str(len(self.guild.threads)) +'`'
        information[_("Rules Channel")+':'] =  emojis[bool(self.guild.rules_channel)]
        information[_("Announcements")+':'] = '`'+ str(len([channel for channel in self.guild.text_channels if not channel.is_news])) +'`'
        return information

    async def __await__(self):
        embed = ShakeEmbed.default(self.ctx, )
        recovery = 'https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png'
        embed.set_author(name=str(self.guild), icon_url=getattr(self.guild.icon, 'url', recovery))
        avatars = []
        embed.set_thumbnail(url=getattr(self.guild.icon, 'url', recovery))
        if self.guild.icon and not self.guild.icon.is_animated():
            for i, formattype in enumerate(list(get_args(ValidStaticFormatTypes)), 1):
                avatars.append(f"[{str(formattype).upper()}]({self.guild.icon.replace(size=1024, static_format=f'{formattype}')})")
            avatars = '**(**' + '|'.join(avatars) + "**)**"
        elif self.guild.icon and self.guild.icon.is_animated():
            avatars = "([GIF]({link}))".format(
                link=self.guild.icon.url
            )
        embed.description = _(
            "**Avatar:** {avatars}\n**Name**: `{name}`"
        ).format(avatars=avatars if bool(avatars) else '', name=self.guild.name)

        list_ = []
        emoji1 = PartialEmoji(name='1_', id=1039247787503648798)
        emoji3 = PartialEmoji(name='3_', id=1039247902217867374)
        
        
        channels = self.channelinfo()
        for x, y in channels.items():
            emoji = (emoji1 if x == list(channels.keys())[-1] else emoji3) if not self.guild.splash else ''
            list_.append(f'{emoji} {"**"+ x +"**" if x else ""}  {y}')
        embed.insert_field_at(index=0, inline=True, name=_("Channel info"), value="\n".join(list_))
        list_.clear()

        information = self.information()
        for x, y in information.items():
            emoji = (emoji1 if x == list(information.keys())[-1] else emoji3) if not self.guild.splash else ''
            list_.append(f'{emoji} {"**"+ x +"**" if x else ""}  {y}')
        embed.insert_field_at(index=0, inline=True, name=_("Information"), value="\n".join(list_))

        if self.guild.splash: 
            embed.set_image(url=self.guild.splash.url)
        else: 
            embed.add_field(name='\u200b', value=self.ctx.bot.config.embed.footer, inline=False)
        
        # TODO: self.guild.features, self.guild.explicit_content_filter is not ContentFilter.disabled)


        await self.ctx.smart_reply(embed=embed)
#
############