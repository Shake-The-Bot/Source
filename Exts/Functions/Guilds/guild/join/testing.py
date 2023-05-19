############
#
from contextlib import suppress
from typing import Optional
from discord import Guild, TextChannel, PartialEmoji, Forbidden, HTTPException, Webhook, NotFound
from Classes.i18n import _
from re import compile, escape
from Classes.database import db
from Classes import ShakeBot, ShakeEmbed
########
#
class Event():
    def __init__(self, bot: ShakeBot, guild: Guild, channel: Optional[TextChannel]=None):
        self.channel: Optional[TextChannel] = channel
        self.bot: ShakeBot = bot
        self.guild: Guild = guild
    
    async def __await__(self):
        # // logging
        rep = dict((escape(k), '') for k in ['discord', 'Discord', 'everyone', 'Everyone']) 
        guild_name = compile("|".join(rep.keys())).sub(lambda m: rep[escape(m.group(0))], self.guild.name)
        webhooks = list(filter(lambda item: item is not None, [Webhook.from_url(url, client=self.bot) for url in self.bot.config.bot.webhook_urls]))
        for webhook in webhooks:
            try:
                await webhook.edit(name=guild_name, avatar=await self.guild.icon.read(), reason='Logs')
            except (HTTPException, NotFound, ValueError, AttributeError):
                continue
            else:
                with suppress(HTTPException, NotFound):
                    await webhook.send('{emoji} Joined `{name}`. I\'m now in {guilds} guilds (+{users} users).'.format(
                        emoji=PartialEmoji(animated=True, name='blobjoin', id=1058033663675207820), name=guild_name, guilds=len(self.bot.guilds), users=self.guild.member_count
                    ))
            
            

        # „I need to find a perfect place for introdoucing myself“
        def introdoucing():
            with suppress(AttributeError):
                if self.channel: 
                    return self.channel
                for chat in self.guild.text_channels:
                    if chat.permissions_for(self.guild.default_role).send_messages and chat.permissions_for(self.guild.default_role).read_messages:
                        return chat
                for chat in self.guild.text_channels:
                    if chat.permissions_for(self.bot.user).send_messages:
                        return chat
                return self.guild.owner
        
        stroke = PartialEmoji(name='bindestrichweiss', id=1041723364244467803)
        point = PartialEmoji(name='white_dot', id=1041719818547642398)
        heart = PartialEmoji(animated=True, name='whiteheart', id=952690616456855573)

        embed = ShakeEmbed(fields=[
            ("{stroke} Start".format(point=point, stroke=stroke), 
            "{point} You can start by getting an overview of all my commands with !help\n\u200b".format(point=point, stroke=stroke))
        ])
        embed.set_thumbnail(url=getattr(self.guild.icon, 'url', None))
        embed.set_author(
            name='Shake just has arrived 〢 First welcome message',
            icon_url=PartialEmoji(animated=True, name='thanks', id=984980175525666887).url
        )
        embed.description = """
            Hello There! Thanks for inviting me to your beautiful server! {emoji}
            I think we can top that!

            {point} First of all, **no** dashboard is required! 
            *You can set up any feature on your Discord server by running the appropriate command*

            **Before you start, you can change the language for the server by typing...**
            ```/language set <the language> server: True```

            To get started properly, you should take a look at the steps under **Start** as they are **honestly** useful 
            
            Finally, if you have any problems with the bot, you can **[join my Discord server here]({invite})** and ask for help.
            """.format(point=point, invite=self.bot.config.other.server, emoji=heart)

        await introdoucing().send(embed=embed)
    
        # „Database stuff“
        with suppress(Exception):
            if self.bot.cache['pools'].get(self.guild.id, None):
                await db.delete_database(self.guild.id,)
            await self.bot.get_pool(self.guild.id)
#
############