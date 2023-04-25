############
#
from Classes import ShakeBot, ShakeContext, ShakeEmbed
from random import sample, choice
from typing import Optional, Literal
from discord import Colour, ui, PartialEmoji, ButtonStyle, Interaction
from .utils.wouldyous import useful, useless
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


    async def set_stats(self, message):
        self.reactions = (await self.ctx.channel.fetch_message(message.id)).reactions

        yes = self.reactions[0]
        no  = self.reactions[1]
        
        yusers: list = [user async for user in yes.users() if not user.bot]
        nusers: list = [user async for user in no.users() if not user.bot]

        self.usersy: list = [x for x in yusers if x not in nusers]
        self.usersn: list = [x for x in nusers if x not in yusers]
        
        self.total: int = len(set(self.usersy+self.usersn))

        self.positive: int = round((len(self.usersy) / (self.total or 1)) * 100)
        self.negative: int = round((len(self.usersn) / (self.total or 1)) * 100)

        self.stats: Optional[bool] = None if (self.positive == self.negative) else self.positive > 50


class VoteView(ui.View):
    def __init__(self, ctx, voting, key):
        super().__init__(timeout=20)
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.key: str = key
        self.voting = voting
        self.no: list = list()
        self.yes: list = list()

    async def set_stats(self, message):

        nusers: list = [user for user in self.no if not user.bot]
        yusers: list = [user for user in self.yes if not user.bot]

        self.yes: list = [x for x in yusers if x not in nusers]
        self.no: list = [x for x in nusers if x not in yusers]
        
        self.total: int = len(set(self.yes+self.no))

        self.positive: int = round((len(self.yes) / (self.total or 1)) * 100)
        self.negative: int = round((len(self.no) / (self.total or 1)) * 100)

        self.stats: Optional[bool] = None if (self.positive == self.negative) else self.positive > 50
        self.tie = self.stats == None

    async def on_timeout(self) -> None:
        if self.voting:
            await self.set_stats(self.message)
            if self.stats == True:
                value = "**{yes}** of **{total}** user(s) (**{procent}**) would take this {key} {emoji}"
            elif self.stats == False: 
                value = "**{no}** of **{total}** user(s) (**{procent}**) would not take this {key} {emoji}"
            else:
                if self.total == 0:
                    value = "**No one** would take this {key}? <:blobsad:1056292826574504066>"
                else:
                    value = "With a total of {total} user(s) a **tie** has been reached (**{procent}**) {emoji}"
            procent = str(self.positive if self.stats == True else self.negative)+'%' if not self.tie else ('50/50' if not self.total == 0 else None)
            emoji = (self.bot.emojis.hook if self.stats == True else self.bot.emojis.cross) if not self.tie else self.bot.emojis.slash
            self.embed.insert_field_at(
                name="Results", inline=False, index=1, value=value.format(
                    procent=procent, total=self.total, yes=len(self.yes), no=len(self.no), key=self.key, emoji=emoji
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


    @ui.button(emoji=PartialEmoji(name='hook', id=1092840629047922688), style=ButtonStyle.green, row=1)
    #@ui.button(emoji=PartialEmoji(animated=True, name='yes', id=1056980221095587891), style=ButtonStyle.green, row=1)
    async def send_yes(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        if not interaction.user in self.yes:
            self.yes.append(interaction.user)
        if interaction.user in self.no:
            self.no.remove(interaction.user)
        return



    @ui.button(emoji=PartialEmoji(name='cross', id=1092840626787197060), style=ButtonStyle.red, row=1)
    #@ui.button(emoji=PartialEmoji(animated=True, name='no', id=1056980224308412496), style=ButtonStyle.red, row=1)
    async def send_no(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        if not interaction.user in self.no:
            self.no.append(interaction.user)
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
        self.u1: list = list()
        self.u2: list = list()


    async def set_stats(self, message):
        users1: list = [user for user in self.u1 if not user.bot]
        users2: list = [user for user in self.u2 if not user.bot]

        self.u1: list = [x for x in users1 if x not in users2]
        self.u2: list = [x for x in users2 if x not in users1]
        
        self.total: int = len(set(self.u1+self.u2))

        self.percentage1: int = round((len(self.u1) / (self.total or 1)) * 100)
        self.percentage2: int = round((len(self.u2) / (self.total or 1)) * 100)
        
        self.procent = self.percentage1 if self.percentage1 >= self.percentage2 else self.percentage2
        self.power = (1 if self.percentage1 >= self.percentage2  else 2)
        self.users = (len(self.u1) if self.percentage1 >= self.percentage2  else len(self.u2))


    async def on_timeout(self) -> None:
        if self.voting:
            await self.set_stats(self.message)

            self.embed.insert_field_at(
                name="Results", inline=False, index=2,
                value=(
                ("**{users}** of **{total}** user(s) (**{procent}%**) would take {key} nr. {power}") 
                if self.total != 0 else ("No one would take any {key}? <:blobsad:1056292826574504066>")).format(
                    procent=self.procent, users=self.users, power=self.power, total=self.total, key=self.key
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
            self.u1.append(interaction.user)
        if interaction.user in self.u2:
            self.u2.remove(interaction.user)
        return


    @ui.button(emoji='2️⃣', style=ButtonStyle.blurple, row=1)
    async def send_no(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        if not interaction.user in self.u2:
            self.u2.append(interaction.user)
        if interaction.user in self.u1:
            self.u1.remove(interaction.user)
        return