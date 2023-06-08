from typing import Optional

from discord import Forbidden, HTTPException, PartialEmoji, TextChannel

from Classes import ShakeBot, ShakeContext, ShakeEmbed, Slash, TextFormat, _

############
#


class command:
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def setup(
        self,
        channel: Optional[TextChannel],
        goal: Optional[int],
        hardcore: bool,
        numbers: bool,
    ):
        if not channel:
            try:
                channel = await self.ctx.guild.create_text_channel(
                    name="counting", slowmode_delay=5
                )
            except (
                HTTPException,
                Forbidden,
            ):
                await self.ctx.chat(
                    _(
                        "The Counting-Game couldn't setup because I have no permissions to do so."
                    )
                )
                return False

        async with self.ctx.db.acquire() as connection:
            query = """INSERT INTO counting (channel_id, guild_id, goal, hardcore, numbers) VALUES ($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING"""
            await connection.execute(
                query,
                channel.id,
                self.ctx.guild.id,
                goal,
                hardcore,
                numbers,
            )

        await self.ctx.chat(
            _("The Counting-Game is succsessfully setup in {channel}").format(
                channel=self.channel.mention
            )
        )

    async def info(self, ctx: ShakeContext) -> None:
        slash = await Slash(ctx.bot).__await__(ctx.bot.get_command("counting"))

        setup = ctx.bot.get_command("counting setup")
        cmd, setup = await slash.get_sub_command(setup)

        counting = ctx.bot.get_command("configure")
        cmd, configure = await slash.get_sub_command(setup)

        embed = ShakeEmbed()
        embed.title = TextFormat.blockquotes(_("Welcome to „Counting“"))
        embed.description = (
            TextFormat.italics(
                _("Thanks for your interest in the game in this awesome place!")
            )
            + " "
            + str(PartialEmoji(name="wumpus", id=1114674858706616422))
        )
        embed.add_field(
            name=_("How to setup the game?"),
            value=_(
                "Get started by using the command {command} to create and setup the essential channel"
            ).format(command=setup),
            inline=False,
        )
        embed.add_field(
            name=_("How to use the game?"),
            value=_(
                "This game is all about numbers, which are posted one after the other in order by different users in the chat"
            ),
            inline=False,
        )
        embed.add_field(
            name=_("How to configure the game?"),
            value=_(
                "Customize all kind of properties for „Counting“ by using the the command {command}!"
            ).format(command=configure),
            inline=False,
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/946862628179939338/1060213944981143692/banner.png"
        )
        await ctx.send(embed=embed, ephemeral=True)

    async def configure(self):
        pass


#
############
