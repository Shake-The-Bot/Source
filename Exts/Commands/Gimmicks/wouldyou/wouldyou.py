############
#
from Classes import ShakeBot, ShakeContext, ShakeEmbed
from Classes.useful import TextFormat, FormatTypes
from random import sample, choice
from typing import Optional, Literal
from discord import Colour, ui, PartialEmoji, ButtonStyle, Interaction
from .utils.wouldyous import useful, useless
b = lambda t: TextFormat.format(t, type=FormatTypes.bold)
########
#
class command():
    def __init__(self, ctx, utility: Literal['useful', 'useless'], voting: bool, rather: bool):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.utility: Literal['useful', 'useless'] = utility
        self.voting: bool = voting
        self.rather: bool = rather


    async def __await__(self):
        utilitys = {'useful': useful, 'useless': useless}.get(self.utility)
        key = choice(list(useless.keys()))
        q1, q2 = sample(utilitys[key], 2)
        embed = ShakeEmbed.default(self.ctx)
        embed.set_author(name='Shake', icon_url=self.bot.user.avatar.url)
        
        if self.rather:
            embed.add_field(name="Would you rather have this",value="> :one: {}".format(q1), inline=False)
            embed.add_field(name="or this {utility} {key}?".format(utility=self.utility, key=key),value="> :two: {}".format(q2), inline=False)
        else:
            embed.add_field(name="Would you want this {utility} {key}?".format(utility=self.utility, key=key), value=">>> {}".format(q1), inline=False)

        embed.add_field(name='\u200b', value=self.ctx.bot.config.embed.footer, inline=False)
        
        if self.rather:
            view = RatherView(self.ctx, self.voting, key)
        else:
            view = VoteView(self.ctx, self.voting, key)
        await view.start(embed)


class VoteView(ui.View):
    def __init__(self, ctx: ShakeContext, voting: bool, key: str):
        super().__init__(timeout=20)
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.key: str = key
        self.voting: bool = voting
        self.no = set()
        self.yes = set()

    async def set_stats(self, message):

        nusers: set = set([user for user in self.no if not user.bot])
        yusers: set = set([user for user in self.yes if not user.bot])

        self.yes: set = set([x for x in yusers if x not in nusers])
        self.no: set = set([x for x in nusers if x not in yusers])
        
        self.total: int = len(self.yes|self.no)

        self.positive: int = round((len(self.yes) / (self.total or 1)) * 100)
        self.negative: int = round((len(self.no) / (self.total or 1)) * 100)

        self.stats: Optional[bool] = None if (self.positive == self.negative) else self.positive > 50
        self.tie = self.stats == None

    async def on_timeout(self) -> None:
        if self.voting:
            await self.set_stats(self.message)
            if self.stats == True:
                value = "{emoji} {yes} of {total} user(s) ({procent}) would take this {key}"
            elif self.stats == False: 
                value = "{emoji} {no} of {total} user(s) ({procent}) would not take this {key}"
            else:
                if self.total == 0:
                    value = "**No one** would take this {key}? <:blobsad:1056292826574504066>"
                else:
                    value = "With a total of {total} user(s) a **tie** has been reached (**{procent}**) {emoji}"
            procent = str(self.positive if self.stats == True else self.negative)+'%' if not self.tie else ('50/50' if not self.total == 0 else None)
            emoji = (self.bot.emojis.hook if self.stats == True else self.bot.emojis.cross) if not self.tie else self.bot.emojis.slash
            self.embed.insert_field_at(
                name="Results", inline=False, index=1, value=value.format(
                    procent=b(procent), total=b(self.total), yes=b(len(self.yes)), no=b(len(self.no)), key=self.key, emoji=emoji
            )   )
            self.embed.colour = (Colour.red() if self.stats == False else Colour.green()) if not self.tie else Colour.light_gray()
            await self.message.edit(embed=self.embed, view=None)
        return await super().on_timeout()

    async def start(self, embed) -> None:
        self.embed = embed
        if not self.voting:
            self.remove_item(self.send_yes)
            self.remove_item(self.send_no)
        self.message = await self.ctx.send(embed=self.embed, view=self)


    @ui.button(emoji=PartialEmoji(name='hook', id=1092840629047922688), style=ButtonStyle.blurple, row=1)
    #@ui.button(emoji=PartialEmoji(animated=True, name='yes', id=1056980221095587891), style=ButtonStyle.blurple, row=1)
    async def send_yes(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        if not interaction.user in self.yes:
            self.yes.add(interaction.user)
        if interaction.user in self.no:
            self.no.remove(interaction.user)
        return



    @ui.button(emoji=PartialEmoji(name='cross', id=1092840626787197060), style=ButtonStyle.blurple, row=1)
    #@ui.button(emoji=PartialEmoji(animated=True, name='no', id=1056980224308412496), style=ButtonStyle.blurple, row=1)
    async def send_no(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        if not interaction.user in self.no:
            self.no.add(interaction.user)
        if interaction.user in self.yes:
            self.yes.remove(interaction.user)
        return


class RatherView(ui.View):
    def __init__(self, ctx: ShakeContext, voting, key):
        super().__init__(timeout=20)
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.key: str = key
        self.voting = voting
        self.u1: set = set()
        self.u2: set = set()


    async def set_stats(self, message):
        users1: set = set([user for user in self.u1 if not user.bot])
        users2: set = set([user for user in self.u2 if not user.bot])

        self.u1: set = set([x for x in users1 if x not in users2])
        self.u2: set = set([x for x in users2 if x not in users1])
        
        self.total: int = len(set(self.u1+self.u2))

        self.percentage1: int = round((len(self.u1) / (self.total or 1)) * 100)
        self.percentage2: int = round((len(self.u2) / (self.total or 1)) * 100)
        
        self.procent = str(self.percentage1 if self.percentage1 >= self.percentage2 else self.percentage2)
        self.power = (1 if self.percentage1 >= self.percentage2  else 2)
        self.users = (len(self.u1) if self.percentage1 >= self.percentage2  else len(self.u2))


    async def on_timeout(self) -> None:
        if self.voting:
            await self.set_stats(self.message)
            emoji = ('1️⃣' if self.power == 1 else '2️⃣') if self.total != 0 else '<:blobsad:1056292826574504066>'
            self.embed.insert_field_at(
                name="Results", inline=False, index=2,
                value=(
                ("{emoji} {users} of {total} user(s) ({procent}) would take {key} nr. {power}") 
                if self.total != 0 else ("{emoji} No one would take any {key}?")).format(
                    procent=b(self.procent+'%'), users=b(self.users), emoji=emoji, power=self.power, total=b(self.total), key=self.key
                )
            )
            self.embed.colour = Colour.og_blurple() if self.total != 0 else Colour.light_gray()
            await self.message.edit(embed=self.embed, view=None)
        return await super().on_timeout()


    async def start(self, embed) -> None:
        self.embed = embed
        if not self.voting:
            self.remove_item(self.send_yes)
            self.remove_item(self.send_no)
        self.message = await self.ctx.send(embed=self.embed, view=self)


    @ui.button(emoji='1️⃣', style=ButtonStyle.blurple, row=1)
    async def send_yes(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        if not interaction.user in self.u1:
            self.u1.add(interaction.user)
        if interaction.user in self.u2:
            self.u2.remove(interaction.user)
        return


    @ui.button(emoji='2️⃣', style=ButtonStyle.blurple, row=1)
    async def send_no(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        if not interaction.user in self.u2:
            self.u2.add(interaction.user)
        if interaction.user in self.u1:
            self.u1.remove(interaction.user)
        return