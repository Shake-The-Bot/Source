from asyncio import TaskGroup
from collections import Counter
from datetime import datetime
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

    async def check(self, game: Literals["counting", "aboveme", "oneword"]):
        cache = self.bot.cache.get(game.capitalize(), dict())
        r = False

        record = MISSING
        if self.channel.id in cache:
            record: dict = cache[self.channel.id]
        else:
            async with self.bot.gpool.acquire() as connection:
                record: dict = await connection.fetchrow(
                    "SELECT * FROM oneword WHERE channel_id = $1",
                    self.channel.id,
                )
        if not bool(record) or not record.get("message_id", None) == self.message.id:
            return False

        last = self.channel.last_message
        if not last:
            lasts = [message async for message in self.channel.history(limit=1)]
            last = lasts[0] if bool(lasts) else None

        if not last:
            return False

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
        cache = self.bot.cache.get("OneWord", dict())

        if self.channel.id in cache:
            record: dict = cache[self.channel.id]
        else:
            async with self.bot.gpool.acquire() as connection:
                record: dict = await connection.fetchrow(
                    "SELECT * FROM oneword WHERE channel_id = $1",
                    self.channel.id,
                )

        words: int = record["words"]
        if not bool(words):
            return True

        word = words[0]

        await self.channel.send(
            _("{user} deleted their word. The word was {word}!").format(
                user=self.message.author.mention,
                word=TextFormat.codeblock(word),
            )
        )
        return True

    async def aboveme(self):
        cache = self.bot.cache.get("AboveMe", dict())

        if self.channel.id in cache:
            record: dict = cache[self.channel.id]
        else:
            async with self.bot.gpool.acquire() as connection:
                record: dict = await connection.fetchrow(
                    "SELECT * FROM aboveme WHERE channel_id = $1",
                    self.channel.id,
                )

        phrase: int = record["phrases"][0]

        await self.channel.send(
            _("{user} deleted their phrase. The phrase was „{phrase}“!").format(
                user=self.message.author.mention, phrase=TextFormat.codeblock(phrase)
            )
        )
        return True

    async def counting(self):
        cache = self.bot.cache.get("Counting", dict())

        if self.channel.id in cache:
            record: dict = cache[self.channel.id]
        else:
            async with self.bot.gpool.acquire() as connection:
                record: dict = await connection.fetchrow(
                    "SELECT * FROM counting WHERE channel_id = $1",
                    self.channel.id,
                )

        count: int = record["count"] or 0

        await self.channel.send(
            _(
                "{user} deleted their count of {count}. The next number is {next}!"
            ).format(
                user=self.message.author.mention,
                count=TextFormat.codeblock(count),
                next=TextFormat.codeblock(count + 1),
            )
        )
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
                "used": str(used.isoformat()),
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
            "used": str(time.isoformat() if passed else used),
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
        if testing and await self.bot.is_owner(member):
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
        count: Optional[int],
        failed: bool,
    ) -> None:
        self.bot.cache["AboveMes"].append(
            {
                "guild_id": guild.id,
                "channel_id": channel.id,
                "user_id": user.id,
                "used": str(used.isoformat()),
                "count": count,
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
            count=count + 1,
            failed=not passed,
        )

        self.cache[self.channel.id]: AboveMeBatch = {
            "used": str(time.isoformat() if passed else used),
            "user_id": member.id if passed else user_id,
            "channel_id": self.channel.id,
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
        if testing and await self.bot.is_owner(member):
            return True
        elif user_id == member.id:
            return False
        return True


#
############
