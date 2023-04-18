############
#
from logging import Filter
########
#
class ApschedulerFilter(Filter):
    def filter(self, record):
        if record.levelname == 'INFO':
            return False
        return True
########
#
class NoMoreRatelimit(Filter):
    def __init__(self):
        super().__init__(name='discord.http')

    def filter(self, record):
        if record.levelname == 'WARNING' and 'rate limit' in record.msg:
            return False
        return True
########
#
class RemoveNoise(Filter):
    def __init__(self, _name):
        super().__init__(name=_name)

    def filter(self, record):
        return False
########
#
class NoMoreAttemps(Filter):
    def __init__(self):
        super().__init__(name='lavalink.websocket')

    def filter(self, record):
        if record.levelname in ('WARNING', 'INFO') and any(snipped in record.msg for snipped in (
            'Invalid response received', 'this may indicate that Lavalink is not running', 'or is running on a port different to the one you provided to', 
            'Attempting to establish WebSocket connection', 'A WebSocket connection could not be established within'
        )):
            return False
        return True
########
#
class NoJobs(Filter):
    def __init__(self) -> None:
        super().__init__(name='apscheduler.scheduler')

    def filter(self, record):
        if record.levelname == 'INFO' and any(snippets in record.msg for snippets in ('Added job', 'Adding job tentatively')):
            return False
        return True
########
#
class NoCommands(Filter):
    def __init__(self):
        super().__init__(name='command')

    def filter(self, record):
        if record.name == ('command') and record.levelname in ('INFO', 'ERROR'): # // ERROR kann raus
            return False
        return True
#
############