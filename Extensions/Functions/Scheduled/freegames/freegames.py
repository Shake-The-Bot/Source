############
#
from typing import List
from Classes import _
from contextlib import suppress
from discord import Guild
from discord.utils import format_dt
from Classes import ShakeBot, ShakeEmbed
from .stores.models import ProductDataType

_images = {
    'epicgames': 'https://cdn.discordapp.com/attachments/672907465670787083/820258283293638676/epic.png',
    'steam': 'https://media.discordapp.net/attachments/672907465670787083/820258285566820402/steam.png',
    'humble': 'https://cdn.discordapp.com/attachments/672907465670787083/820258291862601728/humble.png',
    'gog': 'https://cdn.discordapp.com/attachments/672907465670787083/820258294735962152/gog.png',
    'origin': 'https://cdn.discordapp.com/attachments/672907465670787083/820258290063769600/origin.png',
    'uplay': 'https://cdn.discordapp.com/attachments/672907465670787083/820258286816854046/ubi.png',
    'twitch': 'https://cdn.discordapp.com/attachments/672907465670787083/820258287337472010/twitch.png',
    'itch': 'https://cdn.discordapp.com/attachments/672907465670787083/820258293410299924/itch.png',
    'discord': 'https://cdn.discordapp.com/attachments/672907465670787083/820258296149704714/discord.png',
    'apple': 'https://cdn.discordapp.com/emojis/700097690653949952.png?v=1',
    'google': 'https://cdn.discordapp.com/emojis/700097689194594305.png?v=1',
    'switch': 'https://cdn.discordapp.com/attachments/672907465670787083/820258288938647592/switch.png',
    'ps': None,
    'xbox': None,
    'other': None
}
########
#
class Event():
    def __init__(self, bot: ShakeBot, guild: Guild, games: List[ProductDataType]):
        self.bot: ShakeBot = bot
        self.guild: Guild = guild
        self.games: List[ProductDataType] = games
    
    def divide_chunks(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def embed_from_product(self, game: ProductDataType):
        datetime = game.end # game.end.replace(tzinfo=game.end.tzinfo)
        format_dt_ = format_dt(datetime, "d") if game.end else _("Unknown")
        embed = ShakeEmbed(title=game.title, description = (
            """> {description}
            \u200b
            **~~{price_with_currency}~~** **{discount}** {until} • {storename}
            **[{message}]({url})**""".format(
                message=_("Get free now"), description=game.description, price_with_currency=game.price_with_currency, 
                until=_('until **{datetime}** (GMT)').format(datetime=format_dt_), 
                storename=' '.join([x.capitalize() for x in game.store.split(' ')]),
                url=game.url, discount=_("Free") if (discount := game.discount) == '0' else discount, 
                currency=game.currency #ratings=round(game.rating * 20) / 2,
            )
        ))
        embed.set_thumbnail(url=_images.get(game.store, None))
        embed.set_image(url=game.image)
        
        if (launcher := getattr(game, 'launcher', None)) and launcher is not None:
            embed.add_field(name=_("Or open directly in launcher"), value='**{launcher}**'.format(launcher=launcher))
            
        return embed

    async def __await__(self):
        config = await self.bot.config_pool
        stores: dict = {
            store: {
                game: self.embed_from_product(game)
            } for game in self.games if game.store == store for store in set(game.store for game in self.games)
        }

        for row in config.fetch("SELECT * FROM freegames WHERE guild_id = $1", self.guild.id) or []:
            
            if not (channel := self.bot.get_channel(row.get('channel_id'))):         
                config = await self.bot.config_pool
                config.execute("DELETE FROM freegames WHERE channel_id = $1", row.get('channel_id'))
                continue

            for embeds in self.divide_chunks([stores[store][game] for store in row.get('stores') for game in stores[store]], 10):
                with suppress(Exception):
                    msg = await channel.send(embeds=embeds)
                    await msg.publish()
#
############