from asyncio import TaskGroup
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Tuple

from discord import Guild, Member, Message, TextChannel
from discord.ext.commands import BucketType, CooldownMapping

from Classes import (
    MISSING,
    AboveMeBatch,
    CountingBatch,
    OneWordBatch,
    ShakeBot,
    ShakeEmbed,
    TextFormat,
    _,
    current,
    tens,
)

Literals = Literal["aboveme", "counting", "oneword"]
SystemType = Tuple[Optional[ShakeEmbed], bool, bool]
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
            tg.create_task(self.check(game="oneword"))
        return

    async def check(self, game: Literals):
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
                if (not self.message.content) or bool(self.message.attachments):
                    embed = ShakeEmbed(timestamp=None)
                    embed.description = TextFormat.bold(
                        _(
                            "You should not write anything other than messages with text content!"
                        )
                    )
                    await self.message.reply(embed=embed, delete_after=10)
                    await self.message.delete(delay=10)
                else:
                    func = getattr(self, game, MISSING)
                    if func:
                        r = await func()

        await self.unvalidate(game=game)
        return r

    async def unvalidate(self, game: Literals) -> None:
        async with self.bot.gpool.acquire() as connection:
            unvalids = [
                str(r[0])
                for r in await connection.fetch(
                    f"SELECT channel_id FROM {game} WHERE guild_id = $1",
                    self.guild.id,
                )
                if not self.bot.get_channel(r[0])
            ]

            if unvalids:
                await connection.execute(
                    f"DELETE FROM {game} WHERE channel_id IN {'('+', '.join(unvalids)+')'};",
                )

    async def oneword(self):
        system = OneWord(
            bot=self.bot,
            channel=self.channel,
            guild=self.guild,
            spam_control=CooldownMapping.from_cooldown(10, 12.0, BucketType.user),
        )
        embed, delete, bad_reaction = await system.__await__(
            member=self.author, message=self.message
        )

        if all([_ is None for _ in (embed, delete, bad_reaction)]):
            return

        if not bad_reaction is MISSING:
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

        if all([_ is None for _ in (embed, delete, bad_reaction)]):
            return

        if not bad_reaction is MISSING:
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

        if all([_ is None for _ in (embed, delete, bad_reaction)]):
            return

        if not bad_reaction is MISSING:
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


class OneWord:
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
        self.cache = self.bot.cache["OneWord"]
        self.channel = channel
        self.guild = guild
        self.spam_control = spam_control
        self._auto_spam_count = Counter()

    async def onewords(
        self,
        channel: TextChannel,
        guild: Guild,
        user: Member,
        used: datetime,
        count: Optional[int],
        failed: bool,
    ) -> None:
        self.bot.cache["OneWords"].append(
            {
                "guild_id": guild.id,
                "channel_id": channel.id,
                "user_id": user.id,
                "used": str(used.replace(tzinfo=timezone.utc).isoformat()),
                "count": count,
                "failed": failed,
            }
        )

    async def __await__(self, member: Member, message: Message) -> SystemType:
        content: str = message.clean_content.strip()
        time = message.created_at
        testing: bool = any(
            _.id in set(self.bot.testing) for _ in [self.channel, self.guild, member]
        )

        if self.channel.id in self.cache:
            record: dict = self.cache[self.channel.id]
        else:
            async with self.bot.gpool.acquire() as connection:
                record: dict = await connection.fetchrow(
                    "SELECT * FROM oneword WHERE channel_id = $1",
                    self.channel.id,
                )

        user_id: int = record["user_id"]
        message_id: int = record["message_id"]
        count: int = record["count"] or 0
        words: List[str] = record["words"] or []
        used: datetime = record["used"]
        react: bool = record.get("react", None) or True
        phrase: str = record["phrase"] or ""

        embed = ShakeEmbed(timestamp=None)

        delete = bad_reaction = passed = False

        if not await self.member_check(user_id, member, testing):
            embed.description = TextFormat.bold(
                _("""You are not allowed show off multiple words in a row.""")
            )
            delete = bad_reaction = True

        elif not await self.syntax_check(content):
            embed.description = TextFormat.bold(
                _("your message should contain only one word or punctuation marks.")
            )
            delete = bad_reaction = True

        elif not await self.words_check(content, words):
            embed.description = TextFormat.bold(
                _("Your word should not already be in the sentance.")
            )
            delete = bad_reaction = True

        else:
            passed = True
            if await self.finisher_check(content):
                embed.description = TextFormat.bold(
                    _("You've finally finished the sentence")
                )
                phrase = " ".join(words)
            else:
                embed = None
                words.append(content)

        await self.onewords(
            channel=self.channel,
            guild=self.guild,
            user=member,
            used=time,
            count=count + 1,
            failed=not passed,
        )

        self.cache[self.channel.id]: OneWordBatch = {
            "channel_id": self.channel.id,
            "user_id": member.id if passed else user_id,
            "message_id": message.id if passed else message_id,
            "used": str(
                time.replace(tzinfo=timezone.utc).isoformat() if passed else used
            ),
            "phrase": phrase,
            "words": [] if passed else words,
            "react": react,
            "count": count + 1 if passed else count,
        }

        return embed, delete, bad_reaction if react == True else MISSING

    async def words_check(self, content: str, words: List[str]):
        if content in words:
            return False
        return True

    async def finisher_check(self, content: str):
        finisher = (".", "!", "?")

        if content.startswith(finisher) and content.endswith(finisher):
            return True

        return False

    async def syntax_check(self, content: str):
        digit = content.isdigit()
        if digit:
            return False

        finisher = (".", "!", "?")

        if content.startswith(finisher) and content.endswith(finisher):
            return True

        if any(_ in content for _ in finisher):
            return False

        if len(content.split()) > 1:
            return False

        checks = ["_", "/", "-"]
        for check in checks:
            if len(content.split(check)) > 1:
                return False

        return True

    async def member_check(
        self,
        user_id: int,
        member: Member,
        testing: bool,
    ):
        if testing:
            return True
        elif user_id == member.id:
            return False
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

    async def aboveme(
        self,
        channel: TextChannel,
        guild: Guild,
        user: Member,
        used: datetime,
        phrase: str,
        failed: bool,
    ) -> None:
        self.bot.cache["AboveMes"].append(
            {
                "guild_id": guild.id,
                "channel_id": channel.id,
                "user_id": user.id,
                "used": str(used.replace(tzinfo=timezone.utc).isoformat()),
                "phrase": phrase,
                "failed": failed,
            }
        )

    async def __await__(
        self, member: Member, message: Message
    ) -> Tuple[Optional[ShakeEmbed], bool, bool]:
        content: str = message.clean_content.strip()
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
        message_id: int = record["message_id"]
        count: int = record.get("count", 0)
        used: str = record["used"]
        react: bool = record.get("react", True)
        phrases: List[str] = record.get("phrases", []) or []

        embed = ShakeEmbed(timestamp=None)

        passed = False

        if not await self.member_check(user_id, member, testing):
            embed.description = TextFormat.bold(
                _("""You are not allowed show off multiple numbers in a row.""")
            )

        elif not await self.syntax_check(content):
            embed.description = TextFormat.bold(
                _(
                    "Your message should start with „{trigger}“ and should make sense."
                ).format(
                    trigger=self.trigger.capitalize(),
                )
            )

        elif not await self.phrase_check(content, phrases):
            embed.description = TextFormat.bold(
                _("Your message should be something new")
            )

        else:
            passed = True
            embed = None

            while len(phrases) > 9:
                phrases.pop()
            phrases.insert(0, content)

        await self.aboveme(
            channel=self.channel,
            guild=self.guild,
            user=member,
            used=time,
            phrase=content,
            failed=not passed,
        )

        self.cache[self.channel.id]: AboveMeBatch = {
            "used": str(
                time.replace(tzinfo=timezone.utc).isoformat() if passed else used
            ),
            "user_id": member.id if passed else user_id,
            "channel_id": self.channel.id,
            "message_id": message.id if passed else message_id,
            "phrases": phrases,
            "react": react,
            "count": count + 1 if passed else count,
        }

        return embed, not passed, not passed if react == True else MISSING

    async def phrase_check(self, content: str, phrases: List[str]):
        if content in phrases:
            return False
        return True

    async def syntax_check(self, content: str):
        if not content.lower().startswith(self.trigger.lower()):
            return False

        if not content.lower().removeprefix(self.trigger.lower()):
            return False
        return True

    async def member_check(
        self,
        user_id: int,
        member: Member,
        testing: bool,
    ):
        if testing:
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
        content: str = message.clean_content.strip()
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

        streak: int = record.get("streak", 0) or 0
        best: int = record.get("best", 0) or 0
        user_id: int = record.get("user_id")
        message_id: int = record.get("message_id")
        goal: int = record.get("goal")
        count: int = record.get("count", 0) or 0
        used: datetime = record.get("used")
        react: bool = record.get("react", True)
        numbers: bool = record.get("numbers")
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
                            "You ruined it at {count}. The next number is {backup}. {streak}"
                        ).format(
                            count=TextFormat.underline(record["count"]),
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

        await self.counting(
            channel=self.channel,
            guild=self.guild,
            user=member,
            used=time,
            count=count + 1,
            failed=not passed,
        )

        s = streak + 1 if passed else streak
        self.cache[self.channel.id]: CountingBatch = {
            "used": str(
                time.replace(tzinfo=timezone.utc).isoformat() if passed else used
            ),
            "channel_id": self.channel.id,
            "user_id": member.id if passed else user_id,
            "streak": s,
            "message_id": message.id if passed else message_id,
            "react": react,
            "best": s if s > best else best,
            "count": count + 1 if passed else count,
            "goal": None if reached else goal,
            "numbers": numbers,
        }
        return embed, delete, bad_reaction if react == True else MISSING

    async def counting(
        self,
        channel: TextChannel,
        guild: Guild,
        user: Member,
        used: datetime,
        count: Optional[int],
        failed: bool,
    ) -> None:
        self.bot.cache["Countings"].append(
            {
                "guild_id": guild.id,
                "channel_id": channel.id,
                "user_id": user.id,
                "used": str(used.replace(tzinfo=timezone.utc).isoformat()),
                "count": count,
                "failed": failed,
            }
        )

    async def syntax_check(self, content: str):
        if not content.isdigit():
            return False
        return True

    async def check_number(self, content: str, count: int):
        if not int(content) == count + 1:
            return False
        return True

    async def member_check(self, testing: bool, user_id: int, member: Member):
        if testing:
            return True
        elif user_id == member.id:
            return False
        return True


#
############
