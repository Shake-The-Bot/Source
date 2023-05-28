############
#
from logging import Filter
from typing import Optional, Tuple

__all__ = (
    'NoShards', 'NoAttemps', 'NoJobs', 'NoCommands'
)


def nomore(names: Optional[str] = None, levelnames: Optional[Tuple[str]] = None, messages: Optional[Tuple[str]] = None, mute: Optional[bool] = False):
    class final(Filter):
        def filter(self, record):
            if mute:
                return False
            if names and record.name.lower() in [name.lower() for name in names]:
                return False
            if levelnames and record.levelname.lower() in [levelname.lower() for levelname in levelnames]:
                return False
            if messages and any(msg.lower() in record.msg.lower() for msg in messages):
                return False
            return True
    return final


NoShards = nomore(names=('discord.gateway',), levelnames=('INFO',), messages=('shard id',))()
NoAttemps = nomore(names=('lavalink.websocket',), levelnames=('WARNING', 'INFO',), messages=('Invalid response', 'Lavalink is not running', 'running on a port', 'Attempting to establish', 'connection could not',))()
NoJobs = nomore(names=('apscheduler.scheduler'), levelnames=('INFO',), messages=('Added job', 'Adding job tentatively',))()
NoCommands = nomore(names=('shake.commands',))()
#
############