
############
#
from Classes import _, MISSING
from typing import Union, Literal, get_args, List
from discord import Member, User, PartialEmoji
from discord.utils import format_dt
from Classes import ShakeBot, ShakeEmbed, ShakeContext

ValidStaticFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png']
ValidAssetFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png', 'gif']

########
#

class command():
    def __init__(self, ctx: ShakeContext, user: Union[Member, User]):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.user: Union[Member, User] = user

    def get_badges(self,) -> List[str]:
        badges = [] 
        public_flag = list(self.user.public_flags)

        if self.is_animated or self.banner:
            public_flag.append(('subscriber', True))

        for emoji_name, user_has_flag in public_flag:
            if not user_has_flag: 
                continue
            emoji = getattr(self.bot.emojis.badges, emoji_name, MISSING)
            if emoji is MISSING:
                self.bot.log.critical('[EMOJI IS MISSING] {name}'.format(name=emoji_name))
                continue
            if len(badges) == 0:
                badges.append('︱')
            badges.append(str(emoji))

        return badges

    async def __await__(self):
        embed = ShakeEmbed.default(self.ctx, )
        #embed.set_thumbnail(url=self.user.display_avatar.replace(size=4096))
        embed.set_author(name=str(self.user), icon_url=self.user.display_avatar, url=f"https://discord.com/users/{self.user.id}")
        
        avatars = []
        embed.set_thumbnail(url=self.user.display_avatar.url if self.user.display_avatar else None)
        self.is_animated = getattr(self.user.display_avatar, 'is_animated')() if getattr(self.user.display_avatar, 'is_animated', MISSING) == MISSING else False
        if self.user.display_avatar and not self.is_animated:
            for i, formattype in enumerate(list(get_args(ValidStaticFormatTypes)), 1):
                avatars.append(f"[{str(formattype).upper()}]({self.user.display_avatar.replace(size=1024, static_format=f'{formattype}')})")
            avatars = '**(**' + '|'.join(avatars) + "**)**"
        elif self.user.display_avatar and self.is_animated:
            avatars = "([GIF]({link}))".format(
                link=self.user.display_avatar.url
            )

        self.banner = getattr((await self.bot.fetch_user(self.user.id)), 'banner', None)

        badges = self.get_badges()
    

        embed.description = _(
                """{mention} {badges}
                **Avatar:** {avatars}""").format(
            mention=self.user.mention, avatars=avatars if bool(avatars) else '/', badges=' '.join(badges)
        )
        status = {'idle': _("Idle"), 'dnd': _("Please do not disturb"), 'offline': _("Offline"), 'online': _("Online")}
        emojis = {
            'online': self.bot.emojis.status.online, 'idle': self.bot.emojis.status.idle, 
            'dnd': self.bot.emojis.status.dnd, 'offline': self.bot.emojis.status.offline
        }
        
        xinformation = {
            _("Name")+':': f"`{self.user}`",
            _("#tag")+':': f"`{self.user.discriminator}`",
            _("ID")+':': f"`{self.user.id}`",
            _("Bot")+'?': f"`{_('Yes') if self.user.bot else _('No')}` {'<:on:1037036660455649290>' if self.user.bot else '<:off:1037036665241337858>'} ",
            _("Created")+':': f"<t:{int(self.user.created_at.timestamp())}:R>",
            _("Guilds")+':': f"`{(len(self.user.mutual_guilds)) if not self.user == self.bot.user else _('All')} Shared`",
            _("Discord-System")+'?': f"`{_('Yes') if self.user.system else _('No')}` {'<:on:1037036660455649290>' if self.user.system else '<:off:1037036665241337858>'}"
        }
        emoji1 = PartialEmoji(name='1_', id=1039247787503648798)
        emoji3 = PartialEmoji(name='3_', id=1039247902217867374)

        list_ = []
        for i, (x, y) in enumerate(xinformation.items(), 1):
            emoji = (emoji1 if i == len(xinformation.keys()) else emoji3) if not self.banner else ''
            list_.append(f'{emoji} **{x}**  {y}')
        embed.insert_field_at(index=0, inline=True, name=_("Information"), value="\n".join(list_))
        list_.clear()
        
        if isinstance(self.user, Member):
            permissions = self.user.guild_permissions.value
            yinformation = {
                _("Member")+':': f'`#{sum(m.joined_at < self.user.joined_at for m in self.ctx.guild.members)+1} ({_("of")} {len(self.ctx.guild.members)})`', # if m.joined_at is not None
                _("Since")+':': f'{format_dt(self.user.joined_at, "d")}',
                _("Role")+':': f'{self.user.top_role.mention}',
                _("Color")+':': f'`{self.user.top_role.colour}`',
                _("Perms")+':': '[`{0}`](https://discordapi.com/permissions.html#{0})'.format(permissions),
                _("Activity")+':': f'`{self.user.activity.name if self.user.activity else _("Unknown")}`',
                _("Status")+':': f'`{status.get(str(self.user.status), str(self.user.status))}` {emojis.get(str(self.user.status))}',
                _("Device")+':': f'`{_("📱 Smartphone") if self.user.is_on_mobile() else _("🖥️ Computer")}`'
            }
            for i, (x, y) in enumerate(yinformation.items(), 1):
                emoji = (emoji1 if i == len(yinformation.keys()) else emoji3) if not self.banner else ''
                list_.append(f'{emoji} **{x}**  {y}')
            embed.insert_field_at(index=0, name=_("Server Related"),  inline=True,value="\n".join(list_))

        if self.banner: 
            embed.set_image(url=self.banner.url)
        else: 
            embed.add_field(name='\u200b', value=self.ctx.bot.config.embed.footer, inline=False)
        return await self.ctx.smart_reply(embed=embed)
#
############