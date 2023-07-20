from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from discord import Guild, Member, Message, TextChannel
from discord.ext.commands import BucketType, CooldownMapping

from Classes import MISSING, AboveMeBatch, Format, ShakeBot, ShakeEmbed, _, cleanup

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
        self.game = "AboveMe"

    async def __await__(self):
        ctx = await self.bot.get_context(self.message)

        if ctx and ctx.valid and ctx.command:
            return

        if isinstance(self.channel, TextChannel):
            await self.check()
        return

    async def check(self):
        cache = self.bot.cache.get(self.game, list())

        if self.channel.id in cache:
            done = cache.get(self.channel.id, {}).get("done", None)
            if done:
                return
            await self.aboveme()
        else:
            async with self.bot.gpool.acquire() as connection:
                records: List[int] = [
                    r[0]
                    for r in await connection.fetch(
                        f"SELECT channel_id FROM {self.game.lower()} WHERE guild_id = $1",
                        self.guild.id,
                    )
                ]
            if self.channel.id in records:
                if (not self.message.content) or bool(self.message.attachments):
                    embed = ShakeEmbed(timestamp=None)
                    embed.description = Format.bold(
                        _(
                            "You should not write anything other than messages with text content!"
                        )
                    )
                    await self.message.reply(embed=embed, delete_after=10)
                    await self.message.delete(delay=10)
                else:
                    await self.aboveme()

        await self.unvalidate()
        return True

    async def unvalidate(self) -> None:
        async with self.bot.gpool.acquire() as connection:
            unvalids = [
                str(r[0])
                for r in await connection.fetch(
                    f"SELECT channel_id FROM {self.game} WHERE guild_id = $1",
                    self.guild.id,
                )
                if not self.bot.get_channel(r[0])
            ]

            if unvalids:
                await connection.execute(
                    f"DELETE FROM {self.game} WHERE channel_id IN {'('+', '.join(unvalids)+')'};",
                )

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
            try:
                await self.message.add_reaction(
                    ("☑️", self.bot.emojis.cross)[bad_reaction]
                )
            except:
                pass
        if embed:
            last = self.channel.last_message
            if last:
                descriptions = [embed.description[-22:] for embed in last.embeds]
            else:
                descriptions = []
            if not embed.description[-22:] in descriptions:
                try:
                    await self.message.reply(
                        embed=embed, delete_after=10 if delete else None
                    )
                except:
                    await self.message.channel.send(
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

    async def aboveme(
        self,
        channel: TextChannel,
        guild: Guild,
        user: Member,
        time: datetime,
        phrase: str,
        failed: bool,
    ) -> None:
        self.bot.cache["AboveMes"].append(
            {
                "guild_id": guild.id,
                "channel_id": channel.id,
                "user_id": user.id,
                "used": time.isoformat(),
                "phrase": phrase,
                "failed": failed,
            }
        )

    async def __await__(
        self, member: Member, message: Message
    ) -> Tuple[Optional[ShakeEmbed], bool, bool]:
        content: str = cleanup(message.clean_content.strip())
        time = message.created_at.replace(tzinfo=timezone.utc)
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
        used: datetime = record.get("used") or time
        react: bool = record.get("react", True)
        phrases: List[str] = record.get("phrases", []) or []

        embed = ShakeEmbed(timestamp=None)

        passed = False

        if not await self.member_check(user_id, member, testing):
            embed.description = Format.bold(
                _("""You are not allowed show off multiple numbers in a row.""")
            )

        elif not await self.syntax_check(content):
            embed.description = Format.bold(
                _(
                    "Your message should start with „{trigger}“ and should make sense."
                ).format(
                    trigger=self.trigger.capitalize(),
                )
            )

        elif not await self.phrase_check(content, phrases):
            embed.description = Format.bold(_("Your message should be something new"))

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
            time=time,
            phrase=content,
            failed=not passed,
        )

        self.cache[self.channel.id]: AboveMeBatch = {
            "used": (time if passed else used).isoformat(),
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


#
############
