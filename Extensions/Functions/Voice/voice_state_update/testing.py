############
#
from contextlib import suppress
from datetime import datetime
from typing import Optional, Union

from asyncpg import Pool
from discord import (
    CategoryChannel,
    Forbidden,
    HTTPException,
    Member,
    PermissionOverwrite,
    TextChannel,
    VoiceChannel,
    VoiceState,
)

from Classes import ShakeBot, ShakeEmbed

_ = str


class Event:
    def __init__(
        self, bot: ShakeBot, member: Member, before: VoiceState, after: VoiceState
    ):
        self.member: Member = member
        self.before: VoiceState = before
        self.after: VoiceState = after
        self.bot: ShakeBot = bot

    async def get_creators(self, records) -> Optional[TextChannel | CategoryChannel]:
        valids = dict()
        unvalids = []
        for record in records:
            creator_id = record["creator_id"]
            creator = self.bot.get_channel(creator_id)
            if not creator:
                unvalids.append(creator_id)
                continue
            valids[creator] = record
        for unvalid in unvalids:
            await self.bot.config_pool.execute(
                """DELETE FROM tempvoice WHERE guild_id = $1 AND creator_id = $2""",
                self.member.guild.id,
                unvalid,
            )
        return valids

    async def __await__(self):
        await self.bot.wait_until_ready()

        db: Pool = None
        records = list(
            await self.bot.config_pool.fetch(
                """SELECT * FROM tempvoice WHERE guild_id = $1 AND turn = $2;""",
                self.member.guild.id,
                True,
            )
            or []
        )

        creators: dict[VoiceChannel:Pool] = await self.get_creators(records)

        # zerstören
        if (
            (not self.before.channel is None)
            and (
                self.before.channel.id
                in [
                    y.id for x in creators.keys() for y in x.category.channels
                ]  # getattr(self.before.channel, 'id', None)
            )
            and (
                not any(
                    x in creators.keys()
                    for x in [
                        self.before.channel or None,
                    ]
                )
            )
            and (
                (self.after.channel is None)
                or (self.after.channel != self.before.channel)
            )
            and (not bool(self.before.channel.members))
        ):
            with suppress(Forbidden, HTTPException):
                await self.before.channel.delete()

            # direkt erstellen
            if self.after.channel in creators.keys():
                embed = ShakeEmbed(
                    description=_(
                        "{emoji} {prefix} **Wait before you open another temp channel directly**"
                    ).format(
                        emoji=self.bot.emojis.animated.loading,
                        prefix=self.bot.emojis.prefix,
                    ),
                )
                with suppress(Forbidden, HTTPException):
                    await self.member.move_to(None)
                    await self.member.send(embed=embed)
            deleted = await db.execute(
                """DELETE FROM tempvoice WHERE user_id = $1 RETURNING *;""",
                self.member.id,
            )
            return

        # tempchannel verlassen
        if (
            (not self.before.channel is None)
            and (
                self.before.channel.id
                in [y.id for x in creators.keys() for y in x.category.channels]
            )
            and (
                not any(
                    x in creators.keys()
                    for x in [
                        self.before.channel or None,
                    ]
                )
            )
            and (
                (self.after.channel is None)
                or (self.after.channel != self.before.channel)
            )
        ):
            pass

        # tempchannel beitreten
        if (not self.after.channel is None) and (
            self.after.channel.id
            in [y.id for x in creators.keys() for y in x.category.channels]
        ):
            pass

        # erstellen
        if (not self.after.channel is None) and (self.after.channel in creators.keys()):
            if (
                channel_id := await db.fetchval(
                    "SELECT channel_id FROM tempvoice WHERE user_id = $1;",
                    self.member.id,
                )
                or None is None
            ):
                if channel := self.bot.get_channel(channel_id):
                    embed = ShakeEmbed(
                        description=_(
                            "{emoji} {prefix} **You've already registered a voice channel**".format(
                                prefix=self.bot.emojis.prefix,
                                emoji=self.bot.emojis.cross,
                            )
                        ),
                    )
                    with suppress(Forbidden, HTTPException):
                        await self.member.move_to(channel)
                        return await self.member.send(embed=embed)
                await db.fetchrow(
                    "DELETE FROM tempvoice WHERE channel_id=$1 RETURNING *;", channel_id
                )
            config = await self.bot.config_pool.fetchrow(
                "SELECT * FROM tempvoice WHERE creator_id = $1", self.after.channel.id
            )

            category = (
                self.bot.get_channel(config.get("category_id", None))
                or self.after.channel.category
            )
            name = f"{config.get('prefix', None) or ''} {self.member.display_name} {config.get('suffix', None) or ''}"
            with suppress(Forbidden, HTTPException):  # TODO: if no permissions
                created_channel = await self.member.guild.create_voice_channel(
                    name=name,
                    user_limit=config.get("user_limit", None),
                    category=category,
                    overwrites={
                        self.member.guild.default_role: PermissionOverwrite(
                            view_channel=True,
                            speak=True,
                            connect=not config.get("locked", False),
                            send_messages=True,
                            read_messages=True,
                            read_message_history=True,
                            use_embedded_activities=True,
                        )
                    },
                )
                await self.member.move_to(created_channel)
                await created_channel.set_permissions(
                    self.member,
                    view_channel=True,
                    connect=True,
                    speak=True,
                    send_messages=True,
                    read_messages=True,
                    read_message_history=True,
                    use_embedded_activities=True,
                )
            await db.execute(
                """
                INSERT INTO tempvoice (channel_id, interface_id, creator_id, user_id, time_start, user_limit, privacy, thread, trusted, blocked
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) ON CONFLICT (channel_id) DO NOTHING;""",
                created_channel.id,
                config["interface_id"],
                config["creator_id"],
                self.member.id,
                datetime.now(),
                None,
                not config.get("locked", False),
                False,
                [],
                [],
            )


#
############
