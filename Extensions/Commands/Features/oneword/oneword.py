from typing import Optional

from discord import Forbidden, HTTPException, PartialEmoji, TextChannel

from Classes import ShakeCommand, ShakeEmbed, Slash, TextFormat, _

############
#


class command(ShakeCommand):
    async def setup(self, channel: Optional[TextChannel], react: bool):
        if not channel:
            try:
                channel = await self.ctx.guild.create_text_channel(
                    name="oneword", slowmode_delay=5
                )
            except (
                HTTPException,
                Forbidden,
            ):
                await self.ctx.chat(
                    _(
                        "The OneWord-Game couldn't setup because I have no permissions to do so."
                    )
                )
                return False

        async with self.ctx.db.acquire() as connection:
            query = "SELECT * FROM oneword WHERE channel_id = $1"
            record = await connection.fetchrow(query, channel.id)
            if record:
                await self.ctx.chat(
                    _(
                        "The OneWord-Game couldn't setup because there is alredy one in {channel}."
                    ).format(channel=channel.mention)
                )
                return False

            query = "INSERT INTO oneword (channel_id, guild_id, react) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING"
            await connection.execute(query, channel.id, self.ctx.guild.id, react)

        await self.ctx.chat(
            _("The OneWord-Game is succsessfully setup in {channel}").format(
                channel=channel.mention
            )
        )

    async def info(self) -> None:
        slash = await Slash(self.ctx.bot).__await__(self.ctx.bot.get_command("oneword"))

        setup = self.ctx.bot.get_command("oneword setup")
        cmd, setup = await slash.get_sub_command(setup)

        embed = ShakeEmbed()
        embed.title = TextFormat.blockquotes(_("Welcome to „OneWord“"))
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
                "This game is all about words, which are posted one after the other in the chat to create a creative sentance\n"
            ),
            inline=False,
        )
        rules = [
            _("One person can't post words in a row (others are required)."),
            _("The sentance is done with punctuation marks (eg. „!“)."),
            _("No botting, if you have fail to often, you'll get muted."),
            _("There is no failing."),
        ]
        embed.add_field(
            name=_("OneWord rules"),
            value="\n".join(TextFormat.list(_) for _ in rules),
            inline=False,
        )
        embed.add_field(
            name=_("How to configure the game?"),
            value=_("Currently there is nothing to configure!"),
            inline=False,
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/946862628179939338/1060213944981143692/banner.png"
        )
        await self.ctx.send(embed=embed, ephemeral=True)


#
############
