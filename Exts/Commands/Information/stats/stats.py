############
#
from inspect import cleandoc
from psutil import cpu_percent, virtual_memory
from Classes.i18n import _
from Classes.useful import human_join
from discord import __version__ as dpyversion
from platform import python_version
from humanize import naturalsize
from Classes import ShakeBot, ShakeContext, ShakeEmbed
########
#
class command():
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        owner_ids = self.bot.owner_ids if bool(self.bot.owner_ids) else self.bot.owner_id or []
        owners = human_join(seq=[(await self.bot.get_user_global(owner_id)).mention for owner_id in owner_ids if await self.bot.get_user_global(owner_id)])

        embed = ShakeEmbed.default(self.ctx, title=_("Shake Statistics"), )
        embed.description=cleandoc(f"""
            > [**{_("Support Server Invite")}**]({self.bot.config.other.server})
            > ➥ {_("Official server")}

            > [**{_('Invite bot to the server')}**]({self.bot.config.other.authentication})
            > ➥ {_('Invite Shake Bot')}
            """)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(
            name=_("host"), inline=True,
            value=cleandoc("""```py
                {cpu}: %(cpu)-6s
                {ram}: %(ram)-6s
                ```""" % {
                    'cpu': str(cpu_percent()).split('.')[0]+"%", 'ram': str(naturalsize(virtual_memory().total))
                }).format(
                    cpu=_("cpu"), ram=_("ram")
                ))
        embed.add_field(
            name=_("bot"), inline=True,
            value=cleandoc("""```py
                {server}: %(guild_count)s 
                {user}: %(user)-9s 
                ```""" % {
                    'guild_count': len(self.bot.guilds), 'user': sum(len(guild.members) for guild in self.bot.guilds)
                }).format(
                    server=_("server"), user=_("user")
        ))
        embed.add_field(
            name=_("utils"), inline=True,
            value=cleandoc("""```py
                python: %(python)-5s
                dpy: %(dpy)-5s
                ```""" % {
                    'python': python_version(), 'dpy': dpyversion
        }))
        query = "SELECT used_commands FROM commands WHERE id = $1;"
        embed.add_field(
            name=_("commands"), inline=True,
            value=cleandoc("""```py
                {amount}: %(amout_commands)s
                {used}: %(used_commands)s
                ```""" % {
                    'amout_commands': len(self.bot.commands), 'used_commands': f"{await self.bot.pool.fetchval(query, self.bot.user.id):,}".replace(',', '.')
                }).format(amount=_("amout"), used=_("used")))
        await self.ctx.smart_reply(embed=embed)
#
############