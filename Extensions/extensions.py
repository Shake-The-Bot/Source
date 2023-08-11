from enum import Enum
from functools import partial
from itertools import chain
from typing import Literal

from discord.ext.commands import Bot

extensions = [
    "Extensions.Commands.Help.__init__",
    "Extensions.Commands.Community.community",
    "Extensions.Commands.Community.aboveme.__init__",
    "Extensions.Commands.Community.counting.__init__",
    "Extensions.Commands.Community.oneword.__init__",
    "Extensions.Commands.Community.schedule.__init__",
    "Extensions.Commands.Developing.developing",
    "Extensions.Commands.Developing.bash.__init__",
    "Extensions.Commands.Developing.dispatch.__init__",
    "Extensions.Commands.Developing.extensions.__init__",
    "Extensions.Commands.Developing.leave.__init__",
    "Extensions.Commands.Developing.ptb.__init__",
    "Extensions.Commands.Developing.repl.__init__",
    "Extensions.Commands.Developing.restart.__init__",
    "Extensions.Commands.Developing.rtfm.__init__",
    "Extensions.Commands.Developing.sync.__init__",
    "Extensions.Commands.Gimmicks.gimmicks",
    "Extensions.Commands.Gimmicks.roll.__init__",
    "Extensions.Commands.Gimmicks.everyone.__init__",
    "Extensions.Commands.Gimmicks.say.__init__",
    "Extensions.Commands.Gimmicks.lenght.__init__",
    "Extensions.Commands.Gimmicks.rainbow.__init__",
    "Extensions.Commands.Gimmicks.count.__init__",
    "Extensions.Commands.Gimmicks.random.__init__",
    "Extensions.Commands.Gimmicks.wouldyou.__init__",
    "Extensions.Commands.Gimmicks.scenario.__init__",
    "Extensions.Commands.Information.information",
    "Extensions.Commands.Information.channelinfo.__init__",
    "Extensions.Commands.Information.charinfo.__init__",
    "Extensions.Commands.Information.invite.__init__",
    "Extensions.Commands.Information.ping.__init__",
    "Extensions.Commands.Information.plus.__init__",
    "Extensions.Commands.Information.serverinfo.__init__",
    "Extensions.Commands.Information.hoisters.__init__",
    "Extensions.Commands.Information.stats.__init__",
    "Extensions.Commands.Information.userinfo.__init__",
    "Extensions.Commands.Information.vote.__init__",
    "Extensions.Commands.Information.list.__init__",
    "Extensions.Commands.Moderation.moderation",
    "Extensions.Commands.Moderation.timeout.__init__",
    "Extensions.Commands.Moderation.kick.__init__",
    "Extensions.Commands.Other.other",
    "Extensions.Commands.Other.do.__init__",
    "Extensions.Commands.Other.language.__init__",
    "Extensions.Commands.Other.sudo.__init__",
    "Extensions.Functions.Commands.command.__init__",
    "Extensions.Functions.Commands.command.error.__init__",
    "Extensions.Functions.Commands.command.completion.__init__",
    "Extensions.Functions.Commands.command.delete.__init__",
    "Extensions.Functions.Debug.code_update.__init__",
    "Extensions.Functions.Gateway.dblgg.__init__",
    "Extensions.Functions.Gateway.ready.__init__",
    "Extensions.Functions.Gateway.shard.connect.__init__",
    "Extensions.Functions.Gateway.shard.disconnect.__init__",
    "Extensions.Functions.Gateway.shard.ready.__init__",
    "Extensions.Functions.Gateway.shard.resumed.__init__",
    "Extensions.Functions.Guilds.guild.join.__init__",
    "Extensions.Functions.Guilds.guild.remove.__init__",
    "Extensions.Functions.Interactions.interaction.__init__",
    "Extensions.Functions.Members.member.join.__init__",
    "Extensions.Functions.Messages.message.__init__",
    "Extensions.Functions.Messages.message.aboveme.__init__",
    "Extensions.Functions.Messages.message.counting.__init__",
    "Extensions.Functions.Messages.message.oneword.__init__",
    "Extensions.Functions.Messages.message.edit.__init__",
    "Extensions.Functions.Messages.message.delete.__init__",
    # "Extensions.Functions.Reactions.raw.reaction.add.__init__",
    # "Extensions.Functions.Reactions.raw.reaction.remove.__init__",
    "Extensions.Functions.Scheduled.freegames.__init__",
    # "Extensions.Functions.Voice.voice_state_update.__init__",
]


class Categorys(Enum):
    community = "Community"
    gimmicks = "Gimmicks"
    gimmick = "Gimmicks"
    information = "Information"
    moderation = "Moderation"
    other = "Other"
    others = "Other"
