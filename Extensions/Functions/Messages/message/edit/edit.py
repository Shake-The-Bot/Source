############
#
from asyncio import TaskGroup, sleep
from typing import Any, Literal, Optional

from discord import Guild, Message, TextChannel, Webhook, utils

from Classes import MISSING, ShakeBot, ShakeContext, TextFormat, _, cleanup

########
#

Literals = Literal["AboveMe", "Counting", "OneWord"]


class Event:
    def __init__(self, before: Message, after: Message, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.after = after
        self.before = before
        self.channel: TextChannel = getattr(before, "channel", None) or getattr(
            after, "channel", None
        )
        self.message: Message = before or after
        self.guild: Guild = self.message.guild

    async def __await__(self):
        if self.before.embeds or self.after.embeds:
            return
        if self.before.clean_content.strip() == self.after.clean_content.strip():
            return

        context: ShakeContext = utils.find(
            lambda ctx: ctx.message == self.after, self.bot.cache["context"]
        )
        if context:
            ctx = await context.reinvoke(message=self.after)
        else:
            ctx = await self.bot.process_commands(self.after)

        if ctx and ctx.valid and ctx.command:
            return

        async with TaskGroup() as tg:
            tg.create_task(self.check(game="Counting"))
            tg.create_task(self.check(game="AboveMe"))
            tg.create_task(self.check(game="OneWord"))
        return

    async def check(self, game: Literals):
        cache = self.bot.cache[game]
        if self.channel.id in cache:
            record: dict = cache[self.channel.id]
        else:
            async with self.bot.gpool.acquire() as connection:
                record: dict = await connection.fetchrow(
                    f"SELECT * FROM {game.lower()} WHERE channel_id = $1",
                    self.channel.id,
                )
        if not bool(record):
            return False  # not a game
        if not record.get("message_id", None) == self.message.id:
            return False  # not the latest message of the game

        last: Message = self.channel.last_message
        if not last:
            lasts = [message async for message in self.channel.history(limit=1)]
            try:
                last: Message = lasts[0]
            except KeyError:
                return False

        if last.author == self.bot.user or last.webhook_id:
            return None

        if func := getattr(self, game.lower(), None):
            response = await func(record=record)

        await self.unvalidate(game=game)
        return True

    async def chat(self, webhook_url: Optional[str], **kwargs: Any):
        delete_after = kwargs.pop("delete_after", None)
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

            try:
                message = await webhook.send(wait=True, **kwargs)
                try:
                    await message.add_reaction("☑️")
                except:
                    pass
            except:
                pass
            else:
                await self.message.delete()
            if delete_after:
                await sleep(delete_after)
                await webhook.delete_message(message_id=message.id)

        else:
            try:
                await self.message.reply(delete_after=delete_after, **kwargs)
            except:
                await self.message.channel.send(delete_after=delete_after, **kwargs)

    async def oneword(self, record):
        words: int = record["words"]
        if not bool(words):
            return True
        word = words[0]
        if not cleanup(self.after.content.strip()) == word:
            webhook = record.get("webhook", False)
            content = (
                str(word)
                if bool(webhook)
                else _("{user} edited their word. The word was {word}!").format(
                    user=self.message.author.mention,
                    word=TextFormat.codeblock(word),
                )
            )
            await self.chat(
                webhook_url=webhook,
                content=content,
            )
        return True

    async def aboveme(self, record):
        phrase: int = record["phrases"][0]
        if not cleanup(self.after.content.strip()) == phrase:
            webhook = record.get("webhook", False)
            content = (
                str(phrase)
                if bool(webhook)
                else _("{user} edited their phrase. The phrase was „{phrase}“!").format(
                    user=self.message.author.mention,
                    phrase=TextFormat.codeblock(phrase),
                )
            )
            await self.chat(
                webhook_url=webhook,
                content=content,
            )
        return True

    async def counting(self, record):
        count: int = record.get("count", MISSING) or 0
        direction: bool = record.get("direction", True)
        if not cleanup(self.after.content.strip()) == str(count):
            webhook = record.get("webhook", False)
            content = (
                str(count)
                if bool(webhook)
                else _(
                    "{user} edited their count of {count}. The next number is {next}!"
                ).format(
                    user=self.message.author.mention,
                    count=TextFormat.codeblock(count),
                    next=TextFormat.codeblock(
                        count + (+1 if direction is True else -1)
                    ),
                )
            )
            await self.chat(webhook_url=webhook, content=content)
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


#
############
