import logging
from Classes.logging.filters import NoCommands



class Formatter(logging.Formatter):
    """
    logging Formatter

    >>> logs colourful if streamhandler
    >>> logs with custom format if filehandler
    """

    LEVEL_COLOURS = [
        (logging.DEBUG, "\x1b[40;1m"),
        (logging.INFO, "\x1b[34;1m"),
        (logging.WARNING, "\x1b[33;1m"),
        (logging.ERROR, "\x1b[31m"),
        (logging.CRITICAL, "\x1b[41m"),
    ]

    FORMATS = {
        level: logging.Formatter(
            f"\x1b[30;1m%(asctime)s\x1b[0m > {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)-21s\x1b[0m %(message)s \033[1m[%(filename)s:%(lineno)d]\x1b[0m",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        for level, colour in LEVEL_COLOURS
    }

    def __init__(self, filehandler: bool = False, commandhandler: bool = False, colour: bool = True):
        logging.Formatter.__init__(self)
        self.colour: bool = colour
        self.commandhandler = commandhandler
        self.filehandler: bool = filehandler

    def format(self, record: logging.LogRecord):
        if "bot" in record.name:
            record.name = "discord.shake"
        elif record.name.startswith("Exts."):
            packages = record.name.split('.')
            record.name = packages[2] + '.' + packages[-2]
        formatter = (
            (
                logging.Formatter(
                    "[{asctime}] [{levelname:<8}] {name:<21}: {message}",
                    "%Y-%m-%d - %H:%M:%S",
                    style="{"
                
                ) if self.commandhandler else (
                
                logging.Formatter(
                    "[{asctime}] [{levelname:<8}] {name:<21}: {message} [{filename}:{lineno}]",
                    "%Y-%m-%d - %H:%M:%S",
                    style="{"))
            )
            if self.filehandler
            else self.FORMATS.get(record.levelno) or self.FORMATS[logging.DEBUG]
        )
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f"\x1b[31m{text}\x1b[0m "
        output = formatter.format(record)
        output = output.replace(
            "\x1b[35mdiscord.shake", "\x1b[33mdiscord.shake"
        ).replace(
            "\x1b[35mGateway.ready", "\x1b[33mdiscord.shake"
        )
        if self.filehandler:
            for x in [
                "\x1b[30;1m", "\033[1m", "\x1b[0m", "\x1b[40;1m", "\x1b[34;1m", 
                "\x1b[33;1m", "\x1b[31m", "\x1b[41m", "\x1b[35m", "\x1b[33m",
            ]:
                output = output.replace(x, "")

        record.exc_text = None
        return output

        
formatter = Formatter()
stream = logging.StreamHandler()
stream.setLevel(logging.INFO)
stream.setFormatter(formatter)
stream.addFilter(NoCommands())

def command_handler():
    file_handler_ = logging.FileHandler(filename=f"./Classes/logging/latest/commands.log", encoding="utf-8", mode="w")
    file_handler_.setFormatter(Formatter(filehandler=True, commandhandler=True))
    return file_handler_

def file_handler():
    file_handler_ = logging.FileHandler(filename=f"./Classes/logging/latest/shake.log", encoding="utf-8", mode="w")
    file_handler_.addFilter(NoCommands())
    file_handler_.setFormatter(Formatter(filehandler=True))
    return file_handler_