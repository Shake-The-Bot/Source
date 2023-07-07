from asyncio import TaskGroup, sleep
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

from discord import Guild, Member, Message, TextChannel, Webhook
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
    cleanup,
    current,
    evaluate,
    string_is_calculation,
    tens,
)

Literals = Literal["AboveMe", "Counting", "OneWord"]
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
        self.content = message.content
        self.message = message

    async def __await__(self):
        ctx = await self.bot.get_context(self.message)

        if ctx and ctx.valid and ctx.command:
            return

        if self.bot.user.mentioned_in(self.message) and not bool(
            self.message.attachments
        ):
            content = cleanup(self.content.strip())
            if len(content.split()) == 1:
                content = content.replace(self.bot.user.mention, "", 1)
                if len(content) == 0:
                    message = _("Hey {user}! My prefix is / or {mention}").format(
                        user=self.author.mention,
                        mention=self.bot.user.mention,
                    )
                    try:
                        await self.message.reply(message)
                    except:
                        await self.channel.send(message)
                    finally:
                        return
        if isinstance(self.channel, TextChannel):
            async with TaskGroup() as tg:
                tg.create_task(self.check(game="Counting"))
                tg.create_task(self.check(game="AboveMe"))
                tg.create_task(self.check(game="OneWord"))
        return

    async def check(self, game: Literals):
        cache = self.bot.cache.get(game, list())

        if self.channel.id in cache:
            done = cache.get(self.channel.id, {}).get("done", None)
            if done:
                return
            if func := getattr(self, game.lower(), MISSING):
                await func(game)
            else:
                return False
        else:
            async with self.bot.gpool.acquire() as connection:
                records: List[int] = [
                    r[0]
                    for r in await connection.fetch(
                        f"SELECT channel_id FROM {game.lower()} WHERE guild_id = $1",
                        self.guild.id,
                    )
                ]
            if self.channel.id in records:
                if game == "counting":
                    async with self.bot.gpool.acquire() as connection:
                        done = await connection.fetchval(
                            f"SELECT done FROM {game.lower()} WHERE channel_id = $1",
                            self.channel.id,
                        )
                    if done:
                        return

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
                    if func := getattr(self, game.lower(), MISSING):
                        await func(game)

        await self.unvalidate(game=game)
        return True

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

    async def chat(self, game: Literals, **kwargs: Any):
        cache = self.bot.cache.get(game, list())

        if self.channel.id in cache:
            webhook_url = cache.get(self.channel.id, {}).get("webhook", False)
        else:
            async with self.bot.gpool.acquire() as connection:
                webhook_url = await connection.fetchval(
                    f"SELECT webhook FROM {game.lower()} WHERE channel_id = $1",
                    self.channel.id,
                )

        delete_after = kwargs.pop("delete_after", None)
        print(delete_after)
        if webhook_url:
            webhook = Webhook.from_url(
                webhook_url,
                session=self.bot.session,
                client=self.bot,
                bot_token=self.bot.http.token,
            )

            try:
                await webhook.edit(
                    name=self.author.display_name,
                    avatar=await self.author.display_avatar.read(),
                )
            except:
                pass

            message = await webhook.send(wait=True, **kwargs)
            if delete_after:
                await sleep(delete_after)
                await webhook.delete_message(message_id=message.id)

        else:
            try:
                await self.message.reply(delete_after=delete_after, **kwargs)
            except:
                await self.message.channel.send(delete_after=delete_after, **kwargs)

    async def oneword(self, game: Literals):
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
            if last and last.author == self.bot.user:
                descriptions = [embed.description[-22:] for embed in last.embeds]
            else:
                descriptions = []
            if not embed.description[-22:] in descriptions:
                await self.chat(
                    game=game, embed=embed, delete_after=10 if delete else None
                )
        if delete:
            await self.message.delete(delay=10)
        return True

    async def aboveme(self, game: Literals):
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
                await self.chat(
                    game=game, embed=embed, delete_after=10 if delete else None
                )
        if delete:
            await self.message.delete(delay=10)
        return True

    async def counting(self, game: Literals):
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
                await self.chat(
                    game=game, embed=embed, delete_after=10 if delete else None
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
        failed: bool,
    ) -> None:
        self.bot.cache["OneWords"].append(
            {
                "guild_id": guild.id,
                "channel_id": channel.id,
                "user_id": user.id,
                "used": str(used.replace(tzinfo=timezone.utc).isoformat()),
                "failed": failed,
            }
        )

    async def __await__(self, member: Member, message: Message) -> SystemType:
        content: str = cleanup(message.clean_content.strip())
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
        content: str = cleanup(message.clean_content.strip())
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
        content: str = cleanup(message.clean_content.strip())
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
        start: int = record.get("start", 0) or 0
        used: datetime = record.get("used")
        done: bool = record.get("done", False)
        webhook: bool = record.get("webhook", None) or None
        direction: bool = record.get("direction", True)
        react: bool = record.get("react", True)
        numbers: bool = record.get("numbers")
        math: bool = record.get("math", False)
        restart = reached = False

        current.set(
            await self.bot.locale.get_guild_locale(self.guild.id, default="en-US")
        )

        embed = ShakeEmbed(timestamp=None)
        delete = passed = False
        bad_reaction = 0

        influence = +1 if direction is True else -1

        if not await self.syntax_check(content, math):
            if numbers:
                embed.description = TextFormat.bold(
                    _("You can't use anything but arithmetic here.")
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

        elif not await self.check_number(content, count, direction, math):
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

                if count == start:
                    embed.description = TextFormat.bold(
                        _(
                            "Incorrect number! The next number remains {start}. {streak}"
                        ).format(
                            start=TextFormat.codeblock(f" {start + influence} "),
                            streak=s,
                        )
                    )
                    bad_reaction = 2
                else:
                    embed.description = TextFormat.bold(
                        _(
                            "{user} ruined it at {count}. The next number is {start}. {streak}"
                        ).format(
                            user=member.mention,
                            count=TextFormat.underline(count + influence),
                            streak=s,
                            start=TextFormat.codeblock(f" {start + influence} "),
                        )
                    )
                    bad_reaction = 1
                    user_id = None
                restart = True
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
            elif direction is False and count - 1 <= 0:
                embed.description = TextFormat.bold(
                    _(
                        "You've reached the end of the numbers until 0 {emoji} Congratulations!"
                    ).format(emoji="<a:tadaa:1038228851173625876>")
                )
                done = True
            else:
                embed = None

        new = start if restart else (count + influence) if passed else count

        await self.counting(
            channel=self.channel,
            guild=self.guild,
            user=member,
            direction=direction,
            used=time,
            count=count,
            failed=not passed,
        )

        s = streak + 1 if passed else streak
        self.cache[self.channel.id]: CountingBatch = {
            "used": str(
                time.replace(tzinfo=timezone.utc).isoformat() if passed else used
            ),
            "channel_id": self.channel.id,
            "user_id": member.id if passed else user_id,
            "message_id": message.id if passed else message_id,
            "best": s if s > best else best,
            "count": new,
            "done": done,
            "goal": None if reached else goal,
            "webhook": webhook,
            "streak": s,
            "start": start,
            "direction": direction,
            "react": react,
            "numbers": numbers,
            "math": math,
        }
        return embed, delete, bad_reaction if react == True else MISSING

    async def counting(
        self,
        channel: TextChannel,
        guild: Guild,
        user: Member,
        direction: bool,
        used: datetime,
        count: Optional[int],
        failed: bool,
    ) -> None:
        self.bot.cache["Countings"].append(
            {
                "guild_id": guild.id,
                "channel_id": channel.id,
                "user_id": user.id,
                "direction": direction,
                "used": str(used.replace(tzinfo=timezone.utc).isoformat()),
                "count": count,
                "failed": failed,
            }
        )

    async def syntax_check(self, content: str, math: bool):
        if not content.isdigit():
            if math and string_is_calculation(content):
                return True
            return False
        return True

    async def check_number(self, content: str, count: int, direction: bool, math: bool):
        if math:
            number = evaluate(content)
        else:
            number = int(content)

        if direction is True and not number == count + 1:
            return False

        if direction is False and not number == count - 1:
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
