from asyncio import TaskGroup
from typing import List, Literal, Optional, Tuple

from discord import Guild, Member, Message, PartialEmoji, TextChannel

from Classes import MISSING, ShakeBot, ShakeEmbed, TextFormat, _, current

############
#


class Event:
    def __init__(self, message: Message, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.author: Member = message.author
        self.guild: Guild = message.guild
        self.channel: TextChannel = message.channel
        self.message: Message = message

    async def __await__(self):
        ctx = await self.bot.get_context(self.message)
        if ctx.valid and ctx.command:
            return

        async with TaskGroup() as tg:
            tg.create_task(self.check(game="counting"))
            tg.create_task(self.check(game="aboveme"))
        return

    async def check(self, game: Literal["aboveme", "counting"]):
        cache = self.bot.cache.get(game, list())
        r = False
        if self.channel.id in cache:
            func = getattr(self, game, MISSING)
            if func:
                r = await func()
            else:
                return False
        else:
            async with self.bot.gpool.acquire() as connection:
                records: List[int] = [
                    r[0]
                    for r in await connection.fetch(
                        f"SELECT channel_id FROM {game} WHERE guild_id = $1",
                        self.guild.id,
                    )
                ]
            if self.channel.id in records:
                self.bot.cache.setdefault(game, list())
                self.bot.cache[game].append(self.channel.id)
                func = getattr(self, game, MISSING)
                if func:
                    r = await func()

        await self.unvalidate(game=game)
        return r

    async def unvalidate(self, game: Literal["aboveme", "counting"]) -> None:
        async with self.bot.gpool.acquire() as connection:
            records = [
                r[0]
                for r in await connection.fetch(
                    f"SELECT channel_id FROM {game} WHERE guild_id = $1",
                    self.guild.id,
                )
            ]

            unvalids = [
                str(channel_id)
                for channel_id in records
                if not self.bot.get_channel(channel_id)
            ]
            if unvalids:
                await connection.execute(
                    f"DELETE FROM {game} WHERE channel_id IN {'('+', '.join(unvalids)+')'};",
                )

    # async def await_oneword(self):
    #     oneword = systems.oneword(
    #         member=self.author, message=self.message, bot=self.bot
    #     )
    #     if await oneword.__await__() is False:
    #         return False
    #     delete_message = oneword.do.get("delete_message", False)
    #     add_reaction = oneword.do.get("add_reaction", False)
    #     add_bad = oneword.do.get("add_bad_reaction", False)
    #     with suppress(Forbidden, HTTPException):
    #         if add_bad or add_reaction:
    #             await self.message.add_reaction(
    #                 "☑️" if add_reaction else self.bot.emojis.cross
    #             )
    #         if getattr(oneword, "kwargs", None):
    #             await self.message.channel.send(
    #                 **getattr(oneword, "kwargs"),
    #                 delete_after=10 if delete_message else None
    #             )
    #         if delete_message:
    #             await self.message.delete(delay=10)
    #     return True

    async def aboveme(self):
        system = aboveme(
            bot=self.bot,
            member=self.author,
            channel=self.channel,
            guild=self.guild,
            content=self.message.content,
        )
        embed, delete, bad_reaction = await system.__await__()

        if all([embed is None, delete is None, bad_reaction is None]):
            return

        await self.message.add_reaction(("☑️", self.bot.emojis.cross)[bad_reaction])
        if embed:
            await self.channel.send(embed=embed, delete_after=10 if delete else None)
        if delete:
            await self.message.delete(delay=10)
        return True

    async def counting(self):
        system = counting(
            bot=self.bot,
            member=self.author,
            channel=self.channel,
            guild=self.guild,
            content=self.message.content,
        )
        embed, delete, bad_reaction = await system.__await__()

        if all([embed is None, delete is None, bad_reaction is None]):
            return

        await self.message.add_reaction(
            ("☑️", self.bot.emojis.cross, "⚠️")[bad_reaction]
        )
        if embed:
            await self.channel.send(embed=embed, delete_after=10 if delete else None)
        if delete:
            await self.message.delete(delay=10)
        return True


class aboveme:
    def __init__(
        self,
        bot: ShakeBot,
        member: Member,
        channel: TextChannel,
        guild: Guild,
        content: str,
    ):
        self.bot: ShakeBot = bot
        self.member: Member = member
        self.content: str = content
        self.channel: TextChannel = channel
        self.guild: Guild = guild
        self.testing = any(
            x.id in set(self.bot.testing.keys()) for x in [channel, guild, member]
        )

    async def phrase_check(self, content: str, phrases: List[str]):
        if content.strip() in phrases:
            return False
        return True

    async def syntax_check(self, content: str):
        if not content.lower().startswith(self.trigger.lower()):
            return False

        if not content.lower().removeprefix(self.trigger.lower()).strip():
            return False
        return True

    async def member_check(self, user_id: int):
        if self.testing and await self.bot.is_owner(self.member):
            return True
        elif user_id == self.member.id:
            return False
        return True

    async def __await__(self) -> Tuple[Optional[ShakeEmbed], bool, bool]:
        async with self.bot.gpool.acquire() as connection:
            record = await connection.fetchrow(
                "SELECT * FROM aboveme WHERE channel_id = $1",
                self.channel.id,
            )

        user_id: int = record["user_id"]
        count: int = record["count"] or 0
        phrases: List[str] = record["phrases"] or []
        hardcore: bool = record["hardcore"]

        current.set(
            await self.bot.locale.get_guild_locale(self.guild.id, default="en-US")
        )

        self.trigger: str = _("the one above me")

        embed = ShakeEmbed(timestamp=None)

        delete = bad_reaction = xyz = False

        if not await self.member_check(user_id):
            embed.description = _(
                """{user} ruined it {facepalm} **You can't show off several times in a row**.
                Someone should still go on."""
            ).format(
                user=self.member.mention,
                facepalm=str(PartialEmoji(name="facepalm", id=1038177759983304784)),
            )

            if hardcore:
                embed.description = _(
                    """{user} you are not allowed show off multiple numbers in a row."""
                ).format(user=self.member.mention)
                delete = bad_reaction = True

        elif not await self.syntax_check(self.content):
            embed.description = _(
                "{emoji} Your message should start with „{trigger}“ and should make sense."
            ).format(
                emoji="<a:nananaa:1038185829631266981>",
                trigger=TextFormat.bold(self.trigger.capitalize()),
            )
            delete = bad_reaction = True

        elif not await self.phrase_check(self.content, phrases):
            embed.description = _(
                "{emoji} Your message should be something new"
            ).format(
                emoji="<a:nananaa:1038185829631266981>",
            )
            delete = bad_reaction = True

        else:
            xyz = True
            embed = None

        async with self.bot.gpool.acquire() as connection:
            p = phrases.copy()
            if len(p) >= 10:
                for i in range(len(p[10:-1])):
                    p.pop(i)
            p.insert(0, self.content)

            await connection.execute(
                "UPDATE aboveme SET user_id = $2, phrases = $3, count = $4 WHERE channel_id = $1;",
                self.channel.id,
                self.member.id,
                phrases,
                count + 1 if xyz else count,
            )
        return embed, delete, bad_reaction


class counting:
    def __init__(
        self,
        bot: ShakeBot,
        member: Member,
        channel: TextChannel,
        guild: Guild,
        content: str,
    ):
        self.bot: ShakeBot = bot
        self.member: Member = member
        self.content: str = content
        self.channel: TextChannel = channel
        self.guild: Guild = guild
        self.testing = any(
            x.id in set(self.bot.testing.keys()) for x in [channel, guild, member]
        )

    def tens(self, count: int, last: int = 1):
        if 0 <= count <= 10:
            return 1
        if len(str(count)) <= last:
            last = len(str(count)) - 1
        digits = [int(_) for _ in str(count)]
        for zahl in range(last):
            zahl = zahl + 1
            digits[-zahl] = 0
        return int("".join(str(x) for x in digits))

    async def syntax_check(self, content: str):
        if not content.isdigit():
            return False
        return True

    async def check_number(self, content: str, count: int):
        if not int(content) == count + 1:
            return False
        return True

    async def member_check(self, user_id: int):
        if self.testing and await self.bot.is_owner(self.member):
            return True
        elif user_id == self.member.id:
            return False
        return True

    async def __await__(self):
        async with self.bot.gpool.acquire() as connection:
            record = await connection.fetchrow(
                "SELECT * FROM counting WHERE channel_id = $1",
                self.channel.id,
            )

        streak: int = record["streak"] or 0
        best: int = record["best"] or 0
        user_id: int = record["user_id"]
        hardcore: bool = record["hardcore"]
        goal: int = record["goal"]
        count: int = record["count"] or 0
        numbers: bool = record["numbers"]

        backup: int = self.tens(count)
        reached: bool = False

        current.set(
            await self.bot.locale.get_guild_locale(self.guild.id, default="en-US")
        )

        embed = ShakeEmbed(timestamp=None)
        delete = xyz = False
        bad_reaction = 0

        if not await self.syntax_check(self.content):
            if numbers:
                embed.description = _(
                    "{emoji} You're not allowed to use anything except numbers here"
                ).format(emoji="<a:nananaa:1038185829631266981>")
                delete = True
                bad_reaction = 1
            else:
                return None, None, None

        elif not await self.member_check(user_id):
            embed.description = _(
                "{user} you are not allowed to count multiple numbers in a row."
            ).format(user=self.member.mention)

            delete = True
            if hardcore:
                pass
                # embed.description = _(
                #     """{user} ruined it at **{count}** {facepalm} **You can't count multiple numbers in a row**. The __next__ number {verb} ` {last} `. {streak}""").format(
                #             user=self.member.mention, count=record['count'], facepalm='<:facepalm:1038177759983304784>',
                #             streak=_("**You've topped your best streak with {} 🔥**".format(self.streak)) if self.streak > self.best_streak else '',
                #             verb=(_("is") if not last_ten == record['count'] else _("remains")), last=last_ten)
                # async with db.acquire():
                #     await db.execute(
                #         'UPDATE counting SET user_id = $2, count = $3, streak = 0, best_streak = $4 WHERE channel_id = $1;',
                #         record['channel_id'], self.member.id, last_ten, self.streak if self.streak>self.best_streak else self.best_streak
                #     )
                # delete = bad_reaction = True

        elif not await self.check_number(self.content, count):
            if int(count) in [0, 1]:
                embed.description = _(
                    (
                        "Incorrect number! The __next__ number is ` {last} `. "
                        "**No stats have been changed since the current number was {count}.**"
                        ""
                    )
                ).format(last=backup, count=int(record["count"]) - 1)
                bad_reaction = 2
            else:
                s = ""
                if streak > best:
                    s = TextFormat.bold(
                        _("You've topped your best streak with {} numbers 🔥").format(
                            self.streak
                        )
                    )

                embed.description = _(
                    (
                        "{user} ruined it at **{count}** {facepalm}. "
                        "**You apparently can't count properly**. "
                        "The __next__ number is ` {last} `. {streak}"
                    )
                ).format(
                    user=self.member.mention,
                    count=record["count"],
                    facepalm="<:facepalm:1038177759983304784>",
                    streak=s,
                    last=backup,
                )
                bad_reaction = 1

        else:
            xyz = True

            if goal and count + 1 >= goal:
                reached = True
                embed.description = TextFormat.bold(
                    _(
                        "You've reached your goal of {goal} {emoji} Congratulations!"
                    ).format(goal=goal, emoji="<a:tadaa:1038228851173625876>")
                )
            else:
                embed = None

        async with self.bot.gpool.acquire() as connection:
            s = streak + 1 if xyz else streak
            await connection.execute(
                "UPDATE counting SET user_id = $2, count = $3, streak = $4, best = $5, goal = $6 WHERE channel_id = $1;",
                self.channel.id,
                self.member.id,
                count + 1 if xyz else count,
                s,
                s if s > best else best,
                None if reached else goal,
            )
        return embed, delete, bad_reaction


#
############
