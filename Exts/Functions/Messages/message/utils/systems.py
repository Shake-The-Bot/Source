############
#
from discord import Message, TextChannel, Member, PartialEmoji
from Classes import i18n
from Classes.i18n import _
from Classes import ShakeBot, ShakeEmbed
from typing import Dict
from asyncpg import Pool, Record
########
#
class aboveme():
    def __init__(self, member: Member, bot: ShakeBot, message: Message):
        self.kwargs: dict = {'embeds': []}
        self.do: dict = dict()
        self.message: Message = message
        self.channel: TextChannel = message.channel
        self.member: Member = member
        self.bot: ShakeBot = bot

    async def createrecord(self, db):
        await db.execute('INSERT INTO aboveme (channel_id) VALUES ($1) ON CONFLICT (channel_id) DO NOTHING;', self.channel.id)

    async def clean_channels(self, db, records) -> Dict[TextChannel, Record]: 
        valids = dict()
        unvalids = []
        for record in records:
            channel_id = int(record['channel_id'])
            channel = self.bot.get_channel(channel_id)
            if not channel:
                unvalids.append(channel_id)
                continue
            valids[channel.id] = record
        for unvalid in unvalids:
            query = """DELETE FROM aboveme WHERE channel_id = $1"""
            await db.execute(query, unvalid)
            await self.bot.config_pool.execute(query, unvalid)
        return valids

    async def __await__(self):
        db: Pool = await self.bot.get_pool(_id=self.member.guild.id)
        await self.createrecord(db)
        records = await self.bot.config_pool.fetch(
            'SELECT * FROM aboveme WHERE guild_id = $1 AND turn = $2', 
            self.member.guild.id, True) or []
        channels: Dict[TextChannel: Record] = await self.clean_channels(db, records)
        config = channels.get(self.channel.id, None)
        if config is None: 
            return False # no aboveme configurated for this channel
        record = await db.fetchrow(
            'SELECT * FROM aboveme WHERE channel_id = $1', 
            self.channel.id
        )

        locale = await self.bot.locale.get_guild_locale(self.message.guild.id) or 'en-US'
        i18n.current_locale.set(locale)
        # selber benutzer
        if (record['user_id'] == self.member.id ) and not (await self.bot.is_owner(self.member)): # TODO: Owner-buff
            embed = ShakeEmbed(description = _(
                """{user} you are not allowed show off multiple numbers in a row.""".format(
                    user=self.member.mention
            )))
            self.do['delete_message'] = True
            self.do['add_bad_reaction'] = True
            if config['hardcore']:
                embed.description = _(
                    """{user} ruined it {facepalm} **You can't show off several times in a row**.
                    Someone should still go on.""".format(
                        user=self.member.mention, count=record['count'], 
                        facepalm=str(PartialEmoji(name='facepalm', id=1038177759983304784))
                ))
                self.do['delete_message'] = False
            
            self.kwargs['embeds'].append(embed)
            return True

        # keine zahl & zahlenonly aktiviert
        if (self.message.content.isdigit()) or (not self.message.content.lower().startswith(_('the one above me').lower())):
            embed = ShakeEmbed(description = _("{emoji} Your message should start with **{trigger}**").format(
                emoji='<a:nananaa:1038185829631266981>', trigger=_('the one above me')
            ))
            self.kwargs['embeds'].append(embed)
            self.do['add_bad_reaction'] = True
            self.do['delete_message'] = True
            return True
        
        if (self.message.content in (record.get('phrases', None) or [])):
            embed = ShakeEmbed(description = _("{emoji} Your message should be something new").format(
                emoji='<a:nananaa:1038185829631266981>',
            ))
            self.kwargs['embeds'].append(embed)
            self.do['add_bad_reaction'] = True
            self.do['delete_message'] = True
            return True

        async with db.acquire():
            phrases: list = record.get('phrases', None) or []
            if len(phrases) >= 10:
                phrases.pop(-1); phrases.insert(0, self.message.content)
            await db.execute(
                'UPDATE aboveme SET user_id = $2, phrases = $3 WHERE channel_id = $1;', 
                record['channel_id'], self.member.id, phrases
            )
        self.do['add_reaction'] = True
        return True

class oneword():
    def __init__(self, member: Member, bot: ShakeBot, message: Message):
        self.kwargs: dict = {'embeds': []}
        self.do: dict = dict()
        self.message: Message = message
        self.channel: TextChannel = message.channel
        self.member: Member = member
        self.bot: ShakeBot = bot

    async def createrecord(self, db):
        async with db.acquire():
            await db.execute('INSERT INTO oneword (channel_id) VALUES ($1) ON CONFLICT (channel_id) DO NOTHING;', self.channel.id)

    async def clean_channels(self, db, records) -> Dict[TextChannel, Record]: 
        valids = dict()
        unvalids = []
        for record in records:
            channel_id = int(record['channel_id'])
            channel = self.bot.get_channel(channel_id)
            if not channel:
                unvalids.append(channel_id)
                continue
            valids[channel.id] = record
        for unvalid in unvalids:
            query = """DELETE FROM oneword WHERE channel_id = $1"""
            await db.execute(query, unvalid)
            await self.bot.config_pool.execute(query, unvalid)
        return valids

    async def __await__(self):
        db: Pool = await self.bot.get_pool(_id=self.member.guild.id)
        await self.createrecord(db)
        records = await self.bot.config_pool.fetch(
            'SELECT * FROM oneword WHERE guild_id = $1 AND turn = $2', 
            self.member.guild.id, True) or []
        channels: Dict[TextChannel: Record] = await self.clean_channels(db, records)
        config = channels.get(self.channel.id, None)
        if config is None: 
            return False # no oneword configurated for this channel
        record = await db.fetchrow(
            'SELECT * FROM oneword WHERE channel_id = $1', 
            self.channel.id
        )

        locale = await self.bot.locale.get_guild_locale(self.message.guild.id) or 'en-US'
        i18n.current_locale.set(locale)
        # selber benutzer
        if (record['user_id'] == self.member.id ) and not (await self.bot.is_owner(self.member)): # TODO: Owner-buff
            embed = ShakeEmbed(description = _(
                """{user} you can't change the course of history several times in a row.""".format(
                    user=self.member.mention
            )))
            self.do['delete_message'] = True
            self.do['add_bad_reaction'] = True
            if config['hardcore']:
                embed.description = _(
                    """{user} ruined it {facepalm} **You can't change the course of history several times in a row**.
                    Someone should still go on.""".format(
                        user=self.member.mention, count=record['count'], 
                        facepalm=str(PartialEmoji(name='facepalm', id=1038177759983304784))
                ))
                self.do['delete_message'] = False
            
            self.kwargs['embeds'].append(embed)
            return True

        # nur ein wort
        if (self.message.content.isdigit()) or (not len(self.message.content.split()) == 1) or (
            not self.message.content.startswith(('.', '!', '?')) and self.message.content.endswith(('.', '!', '?'))
        ):
            embed = ShakeEmbed(description = _(
                "{emoji} your message should contain **only one** word").format(
                emoji='<a:nananaa:1038185829631266981>', trigger=_('the one above me')
            ))
            self.kwargs['embeds'].append(embed)
            self.do['add_bad_reaction'] = True
            self.do['delete_message'] = True
            return True

        # if (self.message.content in ('.', '!', '?')) and bool(record.get('words', None) or {}):
        #     embed = ShakeEmbed(description = _("**You've finally finished the sentence {emoji} Congratulations**").format(
        #         emoji='<a:tadaa:1038228851173625876>'
        #     ))
        #     self.kwargs['embeds'].append(embed)
        #     words = set(record.get('words', None) or {})
        #     phrase = ' '.join(words.add(self.message.content))

        async with db.acquire():
            await db.execute(
                'UPDATE oneword SET user_id = $2, count = count+1 WHERE channel_id = $1;', 
                record['channel_id'], self.member.id
            )
        self.do['add_reaction'] = True
        return True

class counting():
    def __init__(self, member: Member, bot: ShakeBot, message: Message):
        self.kwargs: dict = {'embeds': []}
        self.do: dict = dict()
        self.message: Message = message
        self.member: Member = member
        self.channel = message.channel
        self.bot: ShakeBot = bot

    def last_tens_0(self, count: int, last_: int = 1):
        if 0 <= count <= 10: return 1
        if len(str(count)) <= last_: 
            last_ = len(str(count))-1
        digits = [int(_) for _ in str(count)]
        for zahl in range(last_):
            zahl = zahl+1
            digits[-zahl] = 0
        return int(''.join(str(x) for x in digits))

    async def createrecord(self, db):
        async with db.acquire():
            await db.execute('INSERT INTO counting (channel_id) VALUES ($1) ON CONFLICT (channel_id) DO NOTHING;', self.channel.id)

    async def clean_channels(self, db, records) -> Dict[TextChannel, Record]: 
        valids = dict()
        unvalids = []
        for record in records:
            channel_id = int(record['channel_id'])
            channel = self.bot.get_channel(channel_id)
            if not channel:
                unvalids.append(channel_id)
                continue
            valids[channel.id] = record
        for unvalid in unvalids:
            query = """DELETE FROM counting WHERE channel_id = $1"""
            await db.execute(query, unvalid)
            await self.bot.config_pool.execute(query, unvalid)
        return valids

    async def __await__(self):
        db: Pool = await self.bot.get_pool(_id=self.member.guild.id)
        await self.createrecord(db)
        records = await self.bot.config_pool.fetch(
            'SELECT * FROM counting WHERE guild_id = $1 AND turn = $2', 
            self.member.guild.id, True) or []
        channels: Dict[TextChannel: Record] = await self.clean_channels(db, records)
        config = channels.get(self.channel.id, None)
        if config is None: 
            return False # no counting configurated for this channel
        record = await db.fetchrow(
            'SELECT * FROM counting WHERE channel_id = $1', 
            self.channel.id
        )
        
        locale = await self.bot.locale.get_guild_locale(self.message.guild.id) or 'en-US'
        i18n.current_locale.set(locale)
        self.streak = record['streak']
        self.best_streak = record['best_streak']

        # keine zahl & zahlenonly aktiviert
        if (not self.message.content.isdigit()) and (not config['numbersonly']):
            embed = ShakeEmbed(description = _(
                "{emoji} You're not allowed to use anything except numbers here".format(emoji='<a:nananaa:1038185829631266981>')
            ))
            self.kwargs['embeds'].append(embed)
            self.do['delete_message'] = True
            return

        # selber benutzer
        if (record['user_id'] == self.member.id ) and not (await self.bot.is_owner(self.member)):
            last_ten = self.last_tens_0(int(record['count']))
            embed = ShakeEmbed(description = _(
                "{user} you are not allowed to count multiple numbers in a row.").format(
                    user=self.member.mention))
            self.do['delete_message'] = True
            # if config['hardcore']:
            #     embed.description = _(
            #         """{user} ruined it at **{count}** {facepalm} **You can't count multiple numbers in a row**. The __next__ number {verb} ` {last} `. {streak}""").format(
            #                 user=self.member.mention, count=record['count'], facepalm='<:facepalm:1038177759983304784>',
            #                 streak=_("**You've topped your best streak with {} 🔥**".format(self.streak)) if self.streak > self.best_streak else '',
            #                 verb=(_("is") if not last_ten == record['count'] else _("remains")), last=last_ten)
            #     async with db.acquire():
            #         await db.execute(
            #             'UPDATE counting SET user_id = $2, count = $3, streak = 0, best_streak = $4 WHERE channel_id = $1;',
            #             record['channel_id'], self.member.id, last_ten, self.streak if self.streak>self.best_streak else self.best_streak
            #         )
            #     self.do['delete_message'] = False
            #     self.do['add_bad_reaction'] = True
            
            self.kwargs['embeds'].append(embed)
            return

        # falsche zahl
        if (not int(self.message.content) == int(record['count'])):
            last_ten = self.last_tens_0(int(record['count']))

            embed = ShakeEmbed(description=_(
                """{user} ruined it at **{count}** {facepalm}. **You apparently can't count properly**. The __next__ number {verb} ` {last} `. {streak}""").format(
                    user=self.member.mention, count=record['count'], facepalm='<:facepalm:1038177759983304784>', 
                    streak=_("**You've topped your best streak with {} 🔥**".format(self.streak)) if self.streak > self.best_streak else '', 
                    verb=(_("is") if not last_ten == record['count'] else _("remains")), last=last_ten, number=int(self.message.content)
                ) if int(record['count']) != 1 else _(
                    """Incorrect number! The __next__ number is ` {last} `. **No stats have been changed since the current number was {count}.**""".format(
                        last=last_ten, count=int(record['count'])-1)))
            self.kwargs['embeds'].append(embed)

            async with db.acquire():
                await db.execute(
                    'UPDATE counting SET user_id = $2, count = $3, streak = 0, best_streak = $4 WHERE channel_id = $1;',
                    record['channel_id'], self.member.id, last_ten, self.streak if self.streak>self.best_streak else self.best_streak
                )
            self.do['add_bad_reaction'] = True if int(record['count']) != 1 else False
            self.do['add_warning_reaction'] = True if int(record['count']) == 1 else False
            return

        if config['goal'] and int(self.message.content) >= config['goal']:
            embed = ShakeEmbed(description = _(
                "**You've reached your goal of {goal} {emoji} Congratulations**").format(
                    goal=config['goal'], emoji='<a:tadaa:1038228851173625876>'))
                
            self.kwargs['embeds'].append(embed)
            await self.bot.config_pool.execute('UPDATE counting SET goal = $2 WHERE channel_id = $1', record['channel_id'], None)

        async with db.acquire():
            await db.execute(
                'UPDATE counting SET user_id = $2, count = count+1, streak = $3, best_streak = $4 WHERE channel_id = $1;', 
                record['channel_id'], self.member.id, self.streak+1, self.streak if self.streak>self.best_streak else self.best_streak
            )
        self.do['add_reaction'] = True
#
############