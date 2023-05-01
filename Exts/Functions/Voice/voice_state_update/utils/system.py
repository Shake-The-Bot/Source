from discord import TextChannel, Guild, VoiceChannel, Member, PermissionOverwrite
from Classes import ShakeBot
from Classes.i18n import _
from contextlib import suppress
from discord import Interaction, ui, PermissionOverwrite, SelectOption, utils
from typing  import Dict, Set, List
from asyncpg import Pool

class TempVoice():
    def __init__(self, bot: ShakeBot, interface_id: TextChannel.id, member_id: Member.id, guild_id: Guild.id) -> None:
        self.db: Pool
        self.bot = bot
        self.interface_id = interface_id
        self.channel: VoiceChannel
        self.member_id = member_id
        self.member: Member
        self.guild_id = guild_id
        self.guild: Guild

    async def get_channels(self, records): 
        valids = dict()
        unvalids = []
        for record in records:
            channel_id = record['channel_id']
            channel = self.bot.get_channel(channel_id)
            if not channel:
                unvalids.append(channel_id)
                continue
            valids[channel_id] = record
        for unvalid in unvalids:
            await self.bot.config_pool.execute(
                """DELETE FROM tempvoice WHERE guild_id = $1 AND creator_id = $2""", 
                self.member.guild.id, unvalid)
        return valids

    async def __await__(self, interaction):
        self.interaction: Interaction = interaction
        self.db: Pool = await self.bot.get_pool(_id=self.guild_id)  
        records = await self.db.fetch("SELECT * FROM tempvoice")
        self.guild: Guild = self.bot.get_guild(self.guild_id)
        self.member: Member = self.guild.get_member(self.member_id)

        channels: Dict = await self.get_channels(records)
        record = await self.db.fetchrow("SELECT * FROM tempvoice WHERE user_id = $1", self.member_id) or None
        if not self.check(self.member, channels, record):
            return _("{emoji} **Invalid**! You are not in a valid temporary voice channel.").format(
                    emoji=self.bot.emojis.cross)
        self.channel = self.bot.get_channel(record['channel_id'])# if record['channel_id'] in channels.keys() else None

    async def view_check(self, interaction: Interaction) -> VoiceChannel:
        channel = self.bot.get_channel(getattr(self.channel, 'id', None)) or None
        if self.channel is None and not channel:
            await interaction.response.send_message(
                content=_("{emoji} **Invalid**! You are not in a valid temporary voice channel.").format(
                emoji=self.bot.emojis.cross), ephemeral=True)
            return None
        return channel

    def check(self, member, channels, record: Pool = True):
        if not member.voice: 
            return False
        if (not record):
            return False
        if (not bool(channels)):
            return False
        if not (member.voice.channel == self.bot.get_channel(record['channel_id'])):
            return False
        return True
    
    async def rename(self):
        """Change the name of your temporary voice channel"""
        class request(ui.Modal):
            name = ui.TextInput(
                label=_('CHOOSE A NAME FOR YOUR VOICE CHANNEL'), placeholder=_("Leave blank to reset the name"),
                custom_id='tempvoice-rename-request-name', max_length=100, required=False
            )
            def __init__(self, tempvoice: TempVoice) -> None:
                super().__init__(title='TEMPVOICE', timeout=None, custom_id='tempvoice-rename-request')
                self.bot: ShakeBot = tempvoice.bot
                self.check = tempvoice.view_check
                self.member: Member = tempvoice.member
                self.db: Pool = tempvoice.db
                self.channel: VoiceChannel = tempvoice.channel

            async def on_submit(self, interaction: Interaction):
                if not (channel := await self.check(interaction=interaction)):
                    return False

                record = await self.db.fetchrow("SELECT * FROM tempvoice WHERE user_id = $1", self.member.id) #old
                config = await self.bot.config_pool.fetchrow("SELECT * FROM tempvoice WHERE creator_id = $1", record['creator_id'])
                default_name = f"{config.get('prefix', None) or ''} {self.member.display_name} {config.get('suffix', None) or ''}"
                name = str(self.name) if bool(len(str(self.name))) else default_name

                await channel.edit(name=name, reason="TempVoice - executed by {}".format(self.member))

                await interaction.response.send_message(
                    content=_("{emoji} **Updated!** Your channel’s name is now `{name}`!").format(
                    emoji=self.bot.emojis.hook, name=name), ephemeral=True)
                return True

        await self.interaction.response.send_modal(request(self))
    
    async def limit(self):
        """	Change the user limit of your temporary voice channel"""
        
        class request(ui.Modal):
            limit = ui.TextInput(
                label=_('CHOOSE A LIMIT FOR YOUR VOICE CHANNEL'), required=False,
                placeholder=_("Leave blank to reset the limit"), max_length=100
            )
            def __init__(self, tempvoice) -> None:
                super().__init__(title='TEMPVOICE', timeout=None)
                self.bot: ShakeBot = tempvoice.bot
                self.member: Member = tempvoice.member
                self.check = tempvoice.view_check
                self.old_interaction: Interaction = tempvoice.interaction
                self.db: Pool = tempvoice.db
                self.channel: VoiceChannel = tempvoice.channel

            async def on_submit(self, interaction: Interaction):
                if not (channel := await self.check(interaction=interaction)):
                    return False

                _str_limit = str(self.limit) if bool(len(str(self.limit))) else '0'
                if not (_str_limit).isdigit():
                    await interaction.response.send_message(
                        _("{emoji} **Invalid!** ` {value} ` is not a valid Value!!").format(
                        emoji=self.bot.emojis.cross, value=str(self.limit)), ephemeral=True)
                    return

                self.limit = int(round(int(_str_limit), 0))
                
                await channel.edit(user_limit=self.limit if not self.limit == 0 else None, reason="TempVoice - executed by {}".format(self.member))
                await interaction.response.send_message(
                    content=_("{emoji} **Updated!** Your channel’s limit is now ` {limit} `!").format(
                    emoji=self.bot.emojis.hook, limit=str(self.limit) if not self.limit == 0 else _("unlimited")), ephemeral=True)
                return True

        await self.interaction.response.send_modal(request(self))

    async def privacy(self):
        """	Lock or hide your temporary voice channel"""
        class request(ui.Select):
            def __init__(self, tempvoice: TempVoice, options):
                super().__init__(placeholder=_('Select a Privacy Option'), min_values=1, max_values=1, options=options)
                self.channel: VoiceChannel = tempvoice.channel
                self.old_interaction = tempvoice.interaction
                self.bot: ShakeBot = tempvoice.bot
                self.member: Member = tempvoice.member
                self.check = tempvoice.view_check
                self.guild: Guild = tempvoice.guild

            async def callback(self, interaction: Interaction):
                str_values = {'tempvoice-privacy-request-unlocked': _('unlocked'), 'tempvoice-privacy-request-locked': _('locked'), 'tempvoice-privacy-request-invisible': _('invisible'), 'tempvoice-privacy-request-visible': _('visible'),}
                value = self.values[0]

                if not (channel := await self.check(interaction=interaction)):
                    return False

                overwrite = channel.overwrites_for(self.guild.default_role)
                connect = (True if value == 'tempvoice-privacy-request-unlocked' else False) if value in ('tempvoice-privacy-request-locked', 'tempvoice-privacy-request-unlocked') else overwrite.connect
                view_channel = (True if value == 'tempvoice-privacy-request-visible' else False) if value in ('tempvoice-privacy-request-invisible', 'tempvoice-privacy-request-visible') else overwrite.view_channel
                
                await channel.set_permissions(
                    self.guild.default_role, connect=connect, view_channel=view_channel, 
                    speak=overwrite.speak, send_messages=overwrite.send_messages, read_messages=overwrite.read_messages, 
                    read_message_history=overwrite.read_message_history, use_embedded_activities=overwrite.use_embedded_activities,
                    reason="TempVoice - executed by {}".format(self.member))
                await self.old_interaction.edit_original_response(
                    view=None, content=_("{emoji} **Updated!** {channel} is now ` {mode} `!").format(
                        emoji=self.bot.emojis.hook, channel=channel.mention, mode=str_values.get(value)))
                return True
                
        
        class View(ui.View):
            def __init__(self, tempvoice: TempVoice):
                super().__init__()
                self.options: list = []
                self.channel = tempvoice.channel
                self.guild = tempvoice.guild
                self.get_options()
                self.add_item(request(tempvoice=tempvoice, options=self.options))

            def get_options(self):
                overwrite = self.channel.overwrites_for(self.guild.default_role)
                invisible = {'request': overwrite.view_channel == True, 'emoji': '<:invisible:1047200587931975832>', 'label': _('Invisible'), 'description': _('Everyone will be able to view your voice channel'), 'value': 'tempvoice-privacy-request-invisible'}
                visible = {'request': not invisible.get('request'), 'emoji': '<:visible:1047200589668438027>', 'label': _('Visible'), 'description': _('Only trusted users will be able to view your voice channel'), 'value': 'tempvoice-privacy-request-visible'}
                locked = {'request': True if not invisible.get('request', True) else overwrite.connect == True, 'emoji': '<:locked:1047200592604434533>', 'label': _('Lock'), 'description': _('Only trusted users will be able to join your voice channel'), 'value': 'tempvoice-privacy-request-locked'}
                unlocked = {'request': not locked.get('request'), 'emoji': '<:unlocked:1047200591392276530>', 'label': _('Unlock'), 'description': _('Everyone will be able to join your voice channel'), 'value': 'tempvoice-privacy-request-unlocked'}
                for values in [locked, unlocked, invisible, visible]:
                    if values.get('request', False) != False:
                        self.options.append(
                            SelectOption(label=values.get('label'), description=values.get('description'), value=values.get('value', utils.MISSING), emoji=values.get('emoji'))
                        )
        await self.interaction.response.send_message(
            _('{emoji} Use this menu to select an option:').format(
                emoji='<:dot:1047200713979207780>'), view=View(self), ephemeral=True)
        return True
    
    async def transfer(self,):
        """⚡️ Transfer the ownership of your temporary voice channel to another user"""
        class View(ui.View):
            def __init__(self, tempvoice: TempVoice):
                super().__init__()
                self.channel: VoiceChannel = tempvoice.channel
                self.bot: ShakeBot = tempvoice.bot
                self.member: Member = tempvoice.member
                self.db = tempvoice.db
                self.check = tempvoice.view_check
                self.old_interaction: Interaction = tempvoice.interaction
                self.guild: Guild = tempvoice.guild

            @ui.select(
                cls=ui.UserSelect, min_values=1, max_values=1,
                placeholder=_("Selected user will own your tempvoice channel!")
            )
            async def request(self, interaction: Interaction, select: ui.UserSelect):
                if not (channel := await self.check(interaction=interaction)):
                    return False
                
                user = select.values[0]
                record: Dict = await self.db.fetchrow("SELECT * FROM tempvoice WHERE user_id = $1", self.member.id)
                config = await self.bot.config_pool.fetchrow("SELECT * FROM tempvoice WHERE creator_id = $1", record['creator_id'])

                if not (user.voice) or not (user.voice.channel == channel):
                    await self.old_interaction.edit_original_response(
                        view=None, content=_("{emoji} **Invalid**! The selected member is not a valid user in your temporary voice channel.").format(
                            emoji=self.bot.emojis.cross))
                    return False

                overwrites = {
                    self.member: PermissionOverwrite(
                        view_channel=None, connect=None, speak=None, 
                        send_messages=None, read_messages=None, read_message_history=None, use_embedded_activities=None
                    ),
                    user: PermissionOverwrite(
                        view_channel=True, connect=True, speak=True,
                        send_messages=True, read_messages=True, read_message_history=True, use_embedded_activities=True
                    )
                }
                new_name = f"{config.get('prefix', None) or ''} {user.display_name} {config.get('suffix', None) or ''}"

                await self.channel.edit(name=new_name, overwrites=overwrites|channel.overwrites, reason="TempVoice - executed by {}".format(self.member))

                await self.db.execute("UPDATE tempvoice SET user_id = $2 WHERE channel_id = $1", channel.id, user.id)
                await self.old_interaction.edit_original_response(
                    view=None, content=_("{emoji} **Updated!** The {user} is now ` owner ` of your temporary {channel} channel!").format(
                        emoji=self.bot.emojis.hook, user=user.mention, channel=self.channel.mention))
                return True

        await self.interaction.response.send_message(
            _('{emoji} Use this menu to select an option:').format(
                emoji='<:dot:1047200713979207780>'), view=View(self), ephemeral=True)
        return True

    async def trust(self):
        """Trusted users can always join your temporary channel"""
                
        class View(ui.View):
            def __init__(self, tempvoice: TempVoice):
                super().__init__(timeout=None)
                self.channel: VoiceChannel = tempvoice.channel
                self.bot: ShakeBot = tempvoice.bot
                self.member: Member = tempvoice.member
                self.db = tempvoice.db
                self.check = tempvoice.view_check
                self.old_interaction: Interaction = tempvoice.interaction
                self.guild: Guild = tempvoice.guild

            @ui.select(
                cls=ui.UserSelect, placeholder=_("Selected users will be trusted to join!"), 
                min_values=1, max_values=25
            )
            async def request(self, interaction: Interaction, select: ui.UserSelect):
                if not (channel := await self.check(interaction=interaction)):
                    return False

                users: List[Member] = select.values.copy()
                with suppress(ValueError):
                    users.remove(self.member)

                record: Dict = await self.db.fetchrow("SELECT * FROM tempvoice WHERE user_id = $1", self.member.id)
                trusted: Set[int] = set(list(record.get('trusted', None) or {}))
                trusted.update(list(x.id for x in users))
                blocked: List[int] = list(record.get('blocked', None) or {})
                with suppress(ValueError):
                    for user in users:
                        blocked.remove(user.id)
                blocked: Set[int] = set(blocked)
                

                for overwrite in (overwrites := {user: PermissionOverwrite(view_channel=True, connect=True) for user in users}):
                    await channel.set_permissions(target=overwrite, overwrite=overwrites[overwrite], reason="TempVoice - executed by {}".format(self.member))

                await self.db.execute("UPDATE tempvoice SET trusted = $2, blocked = $3 WHERE channel_id = $1", channel.id, trusted, blocked)
                await self.old_interaction.edit_original_response(
                    view=None, content=_("{emoji} **Updated!** The selected users are now ` trusted ` of your temporary {channel} channel!").format(
                        emoji=self.bot.emojis.hook, channel=self.channel.mention))
                return True

        await self.interaction.response.send_message(
            _('{emoji} Use this menu to select an option:').format(
                emoji='<:dot:1047200713979207780>'), view=View(self), ephemeral=True)
        return True
    
    async def block(self):
        """Blocked users are not able to view your temporary voice channel"""
        class View(ui.View):
            def __init__(self, tempvoice: TempVoice):
                super().__init__(timeout=None)
                self.channel: VoiceChannel = tempvoice.channel
                self.bot: ShakeBot = tempvoice.bot
                self.member: Member = tempvoice.member
                self.db = tempvoice.db
                self.check = tempvoice.view_check
                self.old_interaction: Interaction = tempvoice.interaction
                self.guild: Guild = tempvoice.guild

            @ui.select(
                cls=ui.UserSelect, placeholder=_("Selected users will be kicked and blocked!"), 
                min_values=1, max_values=25
            )
            async def request(self, interaction: Interaction, select: ui.UserSelect):
                if not (channel := await self.check(interaction=interaction)):
                    return False

                users: List[Member] = select.values.copy()
                with suppress(ValueError):
                    users.remove(self.member)

                record: Dict = await self.db.fetchrow("SELECT * FROM tempvoice WHERE user_id = $1", self.member.id)
                blocked: Set[int] = set(list(record.get('blocked', None) or {}))
                blocked.update(list(x.id for x in select.values))
                
                trusted: List[int] = list(record.get('trusted', None) or {})
                with suppress(ValueError):
                    for user in users: 
                        trusted.remove(user.id)
                trusted: Set[int] = set(trusted)

                for user in (overwrites := {user: PermissionOverwrite(view_channel=False) for user in users}):
                    await channel.set_permissions(target=user, overwrite=overwrites[user], reason="TempVoice - executed by {}".format(self.member))
                    if user.voice and user.voice.channel == channel:
                        await user.move_to(None, reason="TempVoice - executed by {}".format(self.member))


                await self.db.execute("UPDATE tempvoice SET blocked = $2, trusted = $3 WHERE channel_id = $1", channel.id, blocked, trusted)
                await self.old_interaction.edit_original_response(
                    view=None, content=_("{emoji} **Updated!** The selected users are now ` blocked ` of your temporary {channel} channel!").format(
                        emoji=self.bot.emojis.hook, channel=self.channel.mention))
                return True

        await self.interaction.response.send_message(
            _('{emoji} Use this menu to select an option:').format(
                emoji='<:dot:1047200713979207780>'), view=View(self), ephemeral=True)
        return True

    async def kick(self):
        "⚡️ Kick users from your temporary voice channel"
        
        class View(ui.View):
            def __init__(self, tempvoice: TempVoice):
                super().__init__(timeout=None)
                self.channel: VoiceChannel = tempvoice.channel
                self.bot: ShakeBot = tempvoice.bot
                self.member: Member = tempvoice.member
                self.db = tempvoice.db
                self.check = tempvoice.view_check
                self.old_interaction: Interaction = tempvoice.interaction
                self.guild: Guild = tempvoice.guild

            @ui.select(
                cls=ui.UserSelect, placeholder=_("Selected user will be kicked from your tempvoice channel!"),
                min_values=1, max_values=25
            )
            async def request(self, interaction: Interaction, select: ui.UserSelect):
                
                if not (channel := await self.check(interaction=interaction)):
                    return False

                users: list[Member] = select.values.copy()

                for user in users:
                    if not (user.voice) or not (user.voice.channel == channel) or (user == self.member):
                        with suppress(ValueError):
                            users.remove(user)
                
                if not bool(users):
                    await self.old_interaction.edit_original_response(
                        view=None, content=_("{emoji} **Invalid**! None of the selected users are valid members of your temporary voice channel.").format(
                            emoji=self.bot.emojis.cross))
                    return False

                for user in users:
                    await user.move_to(None, reason="TempVoice - executed by {}".format(self.member))

                await self.old_interaction.edit_original_response(
                    view=None, content=_("{emoji} **Updated!** The selected users got kicked from your temporary {channel} channel!").format(
                        emoji=self.bot.emojis.hook, channel=self.channel.mention))
                return True

        await self.interaction.response.send_message(
            _('{emoji} Use this menu to select an option:').format(
                emoji='<:dot:1047200713979207780>'), view=View(self), ephemeral=True)
        return True

    async def claim(self):
        """⚡️ Claim a temporary voice channel and gain ownership of it"""
        if not self.member.guild_permissions.administrator:
            await self.interaction.response.send_message(
            _('{emoji} this option is only for admins!').format(
                emoji=self.bot.emojis.cross), ephemeral=True)
            return True
        self.channel = getattr(self.member.voice, 'channel', None)
        if not (channel := await self.view_check(interaction=self.interaction)):
            return False
        
        records = await self.db.fetch("SELECT * FROM tempvoice")
        record: Dict = await self.db.fetchrow("SELECT * FROM tempvoice WHERE channel_id = $1", channel.id)
        config = await self.bot.config_pool.fetchrow("SELECT * FROM tempvoice WHERE creator_id = $1", record['creator_id'])
        old_owner = self.guild.get_member(record['user_id'])
        if old_owner == self.member or (self.member.id in list(record['user_id'] for record in records)):
            await self.interaction.response.send_message(
            ephemeral=True, content=_('{emoji} Selected user is alredy owner of a temporary channel!').format(
                emoji=self.bot.emojis.cross))
            return True

        overwrites = {
            self.member: PermissionOverwrite(
                view_channel=True, connect=True, speak=True, 
                send_messages=True, read_messages=True, read_message_history=True, use_embedded_activities=True
            ),
            old_owner: PermissionOverwrite(
                view_channel=None, connect=None, speak=None, 
                send_messages=None, read_messages=None, read_message_history=None, use_embedded_activities=None
            )
        }
        new_name = f"{config.get('prefix', None) or ''} {self.member.display_name} {config.get('suffix', None) or ''}"

        await channel.edit(name=new_name, overwrites=overwrites|channel.overwrites, reason="TempVoice - executed by {}".format(self.member))

        await self.db.execute("UPDATE tempvoice SET user_id = $2 WHERE channel_id = $1", channel.id, self.member.id)
        await self.interaction.response.send_message(
            ephemeral=True, content=_("{emoji} **Updated!** You are now ` owner ` of the temporary {channel} channel!").format(
                emoji=self.bot.emojis.hook, old_owner=old_owner.mention, channel=channel.mention))
        return True

    async def untrust(self):
        """Trusted users can always join your temporary channel (m)"""
                
        class View(ui.View):
            def __init__(self, tempvoice: TempVoice):
                super().__init__(timeout=None)
                self.channel: VoiceChannel = tempvoice.channel
                self.bot: ShakeBot = tempvoice.bot
                self.member: Member = tempvoice.member
                self.db = tempvoice.db
                self.check = tempvoice.view_check
                self.old_interaction: Interaction = tempvoice.interaction
                self.guild: Guild = tempvoice.guild

            @ui.select(
                cls=ui.UserSelect, placeholder=_("Selected users will be untrusted from joining!"), 
                min_values=1, max_values=None
            )
            async def request(self, interaction: Interaction, select: ui.UserSelect):
                if not (channel := await self.check(interaction=interaction)):
                    return False

                users: List[Member] = select.values.copy()
                with suppress(ValueError):
                    users.remove(self.member)
                
                record: Dict = await self.db.fetchrow("SELECT * FROM tempvoice WHERE user_id = $1", self.member.id)
                trusted: Set[int] = set(record.get('trusted', {}))
                for user in users:
                    if user.id in trusted:
                        continue
                    users.remove(user)

                with suppress(ValueError):
                    for user in users: trusted.remove(user.id)
                trusted: Set[int] = set(trusted)

                for overwrite in (overwrites := {user: PermissionOverwrite(view_channel=None, connect=None) for user in select.values}):
                    await channel.set_permissions(overwrite, overwrites[overwrite], reason="TempVoice - executed by {}".format(self.member))

                await self.db.execute("UPDATE tempvoice SET trusted = $2 WHERE channel_id = $2", channel.id, trusted)
                await self.old_interaction.edit_original_response(
                    view=None, content=_("{emoji} **Updated!** The selected users are now ` untrusted ` of your temporary {channel} channel!").format(
                        emoji=self.bot.emojis.hook, channel=channel.mention))
                return True

        await self.interaction.response.send_message(
            _('{emoji} Use this menu to select an option:').format(
                emoji='<:dot:1047200713979207780>'), view=View(self), ephemeral=True)
        return True
    
    async def unblock(self):
        """Blocked users are not able to view your temporary voice channel"""
                
        class View(ui.View):
            def __init__(self, tempvoice: TempVoice):
                super().__init__(timeout=None)
                self.channel: VoiceChannel = tempvoice.channel
                self.bot: ShakeBot = tempvoice.bot
                self.member: Member = tempvoice.member
                self.db = tempvoice.db
                self.check = tempvoice.view_check
                self.old_interaction: Interaction = tempvoice.interaction
                self.guild: Guild = tempvoice.guild

            @ui.select(
                cls=ui.UserSelect, placeholder=_("Selected users will be unblocked from joining!"), 
                min_values=1, max_values=None
            )
            async def request(self, interaction: Interaction, select: ui.UserSelect):
                if not (channel := await self.check(interaction=interaction)):
                    return False

                users: List[Member] = select.values.copy()
                with suppress(ValueError):
                    users.remove(self.member)
                
                record: Dict = await self.db.fetchrow("SELECT * FROM tempvoice WHERE user_id = $1", self.member.id)
                blocked: Set[int] = set(record.get('blocked', {}))
                for user in users:
                    if user.id in blocked:
                        continue
                    users.remove(user)

                with suppress(ValueError):
                    for user in users: blocked.remove(user.id)
                blocked: Set[int] = set(blocked)

                for overwrite in (overwrites := {user: PermissionOverwrite(view_channel=None, connect=None) for user in select.values}):
                    await channel.set_permissions(overwrite, overwrites[overwrite], reason="TempVoice - executed by {}".format(self.member))

                await self.db.execute("UPDATE tempvoice SET blocked = $2 WHERE channel_id = $2", channel.id, blocked)
                await self.old_interaction.edit_original_response(
                    view=None, content=_("{emoji} **Updated!** The selected users are now ` unblocked ` of your temporary {channel} channel!").format(
                        emoji=self.bot.emojis.hook, channel=channel.mention))
                return True

        await self.interaction.response.send_message(
            _('{emoji} Use this menu to select an option:').format(
                emoji='<:dot:1047200713979207780>'), view=View(self), ephemeral=True)
        return True

    # ✘
    async def region(self, region):
        """⚡️ Change the region of your temporary voice channel"""
        await self.channel.edit(region=str(region))
    # ✘
    async def bitrate(self):
        pass #TODO: bitrate