from asyncio import TaskGroup
from collections import Counter
from typing import Dict, List, Literal, Optional, Tuple

from discord import Guild, Member, Message, PartialEmoji, TextChannel
from discord.ext.commands import BucketType, CooldownMapping

from Classes import (
    MISSING,
    CountingBatch,
    ShakeBot,
    ShakeEmbed,
    TextFormat,
    _,
    current,
    human_join,
    tens,
)

############
#


class Event:
    bot: ShakeBot
    guild: Guild
    channel: TextChannel
    message: Message
    spam_control: CooldownMapping

    def __init__(self, message: Message, bot: ShakeBot):
        self.bot = bot
        self.author = message.author
        self.guild = message.guild
        self.channel = message.channel
        self.message = message

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
        system = AboveMe(
            bot=self.bot,
            channel=self.channel,
            guild=self.guild,
            spam_control=CooldownMapping.from_cooldown(10, 12.0, BucketType.user),
        )
        embed, delete, bad_reaction = await system.__await__(
            member=self.author, message=self.message
        )

        if all([embed is None, delete is None, bad_reaction is None]):
            return

        await self.message.add_reaction(("☑️", self.bot.emojis.cross)[bad_reaction])
        if embed:
            last = self.channel.last_message
            if last:
                descriptions = [embed.description[-22:] for embed in last.embeds]
            else:
                descriptions = []
            if not embed.description[-22:] in descriptions:
                await self.message.reply(
                    embed=embed, delete_after=10 if delete else None
                )
        if delete:
            await self.message.delete(delay=10)
        return True

    async def counting(self):
        system = Counting(
            bot=self.bot,
            channel=self.channel,
            guild=self.guild,
            spam_control=CooldownMapping.from_cooldown(10, 12.0, BucketType.user),
        )
        embed, delete, bad_reaction = await system.__await__(
            member=self.author, message=self.message
        )

        if all([embed is None, delete is None, bad_reaction is None]):
            return

        await self.message.add_reaction(
            ("☑️", self.bot.emojis.cross, "⚠️")[bad_reaction]
        )
        if embed:
            last = self.channel.last_message
            if last:
                descriptions = [embed.description[-22:] for embed in last.embeds]
            else:
                descriptions = []
            if not embed.description[-22:] in descriptions:
                await self.message.reply(
                    embed=embed, delete_after=10 if delete else None
                )
        if delete:
            await self.message.delete(delay=10)
        return True


class AboveMe:
    channel: TextChannel
    guild: Guild
    cache: Dict[int, List]
    trigger: str
    spam_control: CooldownMapping

    def __init__(
        self,
        bot: ShakeBot,
        guild: Guild,
        channel: TextChannel,
        spam_control: CooldownMapping,
    ):
        self.bot = bot
        self.cache = self.bot.cache["AboveMe"]
        self.channel = channel
        self.trigger = _("the one above me")
        self.guild = guild
        self.spam_control = spam_control
        self._auto_spam_count = Counter()

    async def __await__(
        self, member: Member, message: Message
    ) -> Tuple[Optional[ShakeEmbed], bool, bool]:
        content: str = message.clean_content
        time = message.created_at
        testing: bool = any(
            _.id in set(self.bot.testing) for _ in [self.channel, self.guild, member]
        )

        if self.channel.id in self.cache:
            record: dict = self.cache[self.channel.id]
        else:
            async with self.bot.gpool.acquire() as connection:
                record: dict = await connection.fetchrow(
                    "SELECT * FROM aboveme WHERE channel_id = $1",
                    self.channel.id,
                )

        user_id: int = record["user_id"]
        count: int = record["count"] or 0
        phrases: List[str] = record["phrases"] or []

        embed = ShakeEmbed(timestamp=None)

        delete = bad_reaction = passed = False

        if not await self.member_check(user_id, member, testing):
            embed.description = TextFormat.bold(
                _("""You are not allowed show off multiple numbers in a row.""")
            )
            delete = bad_reaction = True

        elif not await self.syntax_check(content):
            embed.description = TextFormat.bold(
                _(
                    "Your message should start with „{trigger}“ and should make sense."
                ).format(
                    trigger=self.trigger.capitalize(),
                )
            )
            delete = bad_reaction = True

        elif not await self.phrase_check(content, phrases):
            embed.description = TextFormat.bold(
                _("Your message should be something new")
            )
            delete = bad_reaction = True

        else:
            passed = True
            embed = None

            if len(phrases) >= 10:
                for i in range(len(phrases[10:-1])):
                    phrases.pop(i)
            phrases.insert(0, content)

        self.cache[self.channel.id]: CountingBatch = {
            "channel_id": self.channel.id,
            "user_id": member.id,
            "used": time.isoformat(),
            "phrases": phrases,
            "count": count + 1 if passed else count,
        }

        return embed, delete, bad_reaction

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

    async def member_check(
        self,
        user_id: int,
        member: Member,
        testing: bool,
    ):
        if testing and await self.bot.is_owner(member):
            return True
        elif user_id == member.id:
            return False
        return True


class Counting:
    channel: TextChannel
    guild: Guild
    cache: Dict[int, List]
    spam_control: CooldownMapping

    def __init__(
        self,
        bot: ShakeBot,
        guild: Guild,
        channel: TextChannel,
        spam_control: CooldownMapping,
    ):
        self.bot = bot
        self.cache = self.bot.cache["Counting"]
        self.channel = channel
        self.guild = guild
        self.spam_control = spam_control
        self._auto_spam_count = Counter()

    async def __await__(
        self, member: Member, message: Message
    ) -> Tuple[ShakeEmbed, bool, Literal[1, 2, 3]]:
        content: str = message.clean_content
        time = message.created_at
        testing: bool = any(
            _.id in set(self.bot.testing) for _ in [self.channel, self.guild, member]
        )

        if self.channel.id in self.cache:
            record: dict = self.cache[self.channel.id]
        else:
            async with self.bot.gpool.acquire() as connection:
                record: dict = await connection.fetchrow(
                    "SELECT * FROM counting WHERE channel_id = $1",
                    self.channel.id,
                )

        streak: int = record["streak"] or 0
        best: int = record["best"] or 0
        user_id: int = record["user_id"]
        goal: int = record["goal"]
        count: int = record["count"] or 0
        used: str = record["used"]
        numbers: bool = record["numbers"]
        backup: int = tens(count, True) - 1
        reached: bool = False

        current.set(
            await self.bot.locale.get_guild_locale(self.guild.id, default="en-US")
        )

        embed = ShakeEmbed(timestamp=None)
        delete = passed = False
        bad_reaction = 0

        if not await self.syntax_check(content):
            if numbers:
                embed.description = TextFormat.bold(
                    _("You're not allowed to use anything except numbers here")
                )
                delete = True
                bad_reaction = 1
            else:
                return None, None, None

        elif not await self.member_check(
            testing=testing, user_id=user_id, member=member
        ):
            embed.description = TextFormat.bold(
                _("You are not allowed to count multiple numbers in a row.")
            )
            bad_reaction = 1
            delete = True

        elif not await self.check_number(content, count):
            bucket = self.spam_control.get_bucket(message)
            retry_after = bucket and bucket.update_rate_limit(time.timestamp())
            if retry_after:  # member.id != self.owner_id:
                self._auto_spam_count[member.id] += 1

            if self._auto_spam_count[member.id] >= 5:
                embed.description = TextFormat.bold(
                    _("You failed to often. No stats have been changed!!")
                )
                del self._auto_spam_count[member.id]
                bad_reaction = 2
            else:
                self._auto_spam_count.pop(member.id, None)
                if streak != 0:
                    s = _("The streak of {streak} was broken!")
                    if streak > best:
                        s = _("You've topped your best streak with {streak} numbers 🔥")
                    s = s.format(streak=TextFormat.codeblock(f" {streak} "))
                else:
                    s = ""

                if int(count) == backup:
                    embed.description = TextFormat.bold(
                        _(
                            "Incorrect number! The next number remains {backup}. {streak}"
                        ).format(
                            backup=TextFormat.codeblock(f" {backup + 1} "),
                            streak=s,
                        )
                    )
                    bad_reaction = 2
                else:
                    embed.description = TextFormat.bold(
                        _(
                            "You ruined it at {count} {facepalm}. The next number is {backup}. {streak}"
                        ).format(
                            count=TextFormat.underline(record["count"]),
                            facepalm="<:facepalm:1038177759983304784>",
                            streak=s,
                            backup=TextFormat.codeblock(f" {backup + 1} "),
                        )
                    )
                    bad_reaction = 1
                count = backup
                streak = 0

        else:
            passed = True

            if goal and count + 1 >= goal:
                reached = True
                embed.description = TextFormat.bold(
                    _(
                        "You've reached your goal of {goal} {emoji} Congratulations!"
                    ).format(goal=goal, emoji="<a:tadaa:1038228851173625876>")
                )
            else:
                embed = None

        s = streak + 1 if passed else streak
        self.cache[self.channel.id]: CountingBatch = {
            "channel_id": self.channel.id,
            "user_id": member.id,
            "used": time.isoformat(),
            "streak": s,
            "best": s if s > best else best,
            "count": count + 1 if passed else count,
            "goal": None if reached else goal,
            "numbers": numbers,
        }

        return embed, delete, bad_reaction

    async def syntax_check(self, content: str):
        if not content.isdigit():
            return False
        return True

    async def check_number(self, content: str, count: int):
        if not int(content) == count + 1:
            return False
        return True

    async def member_check(self, testing: bool, user_id: int, member: Member):
        if testing and await self.bot.is_owner(member):
            return True
        elif user_id == member.id:
            return False
        return True


#
############
