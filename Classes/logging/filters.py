############
#
from logging import Filter
from typing import Optional, Tuple

__all__ = (
    'NoShards', 'NoAttemps', 'NoJobs', 'NoCommands'
)


def nomore(n, /, names: Optional[Tuple[str]] = None, levelnames: Optional[Tuple[str]] = None, messages: Optional[Tuple[str]] = None):
    class final(Filter):
        def __init__(self):
            super().__init__(name=n)

        def filter(self, record):
            if names and record.name.lower() in [name.lower() for name in names]:
                return False
            if levelnames and record.levelname.lower() in [levelname.lower() for levelname in levelnames]:
                return False
            if messages and any(msg.lower() in record.msg.lower() for msg in messages):
                return False
            return True
    return final


NoShards = nomore('discord.gateway', levelnames=('INFO'), messages=('shard id'))
NoAttemps = nomore('lavalink.websocket', levelnames=('WARNING', 'INFO'), messages=('Invalid response', 'Lavalink is not running', 'running on a port', 'Attempting to establish', 'connection could not'))
NoJobs = nomore('apscheduler.scheduler', levelnames=('INFO'), messages=('Added job', 'Adding job tentatively'))
NoCommands = nomore('command', names=('command'))
#
############