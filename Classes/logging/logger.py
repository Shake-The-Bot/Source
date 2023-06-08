from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, FileHandler, Filter
from logging import Formatter as Logger
from logging import LogRecord, StreamHandler
from typing import Optional, Tuple

__all__ = ("Formatter", "handler")


class Formatter(Logger):
    """
    logging Formatter

    >>> logs colourful if streamhandler
    >>> logs with custom format if filehandler
    """

    LEVEL_COLOURS = [
        (DEBUG, "\x1b[40;1m"),
        (INFO, "\x1b[34;1m"),
        (WARNING, "\x1b[33;1m"),
        (ERROR, "\x1b[31m"),
        (CRITICAL, "\x1b[41m"),
    ]

    FORMATS = {
        level: Logger(
            f"\x1b[30;1m%(asctime)s\x1b[0m > {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)-21s\x1b[0m %(message)s \033[1m[%(filename)s:%(lineno)d]\x1b[0m",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        for level, colour in LEVEL_COLOURS
    }

    def __init__(self, filehandler: bool = False, colour: bool = True):
        Logger.__init__(self)
        self.colour: bool = colour
        self.filehandler: bool = filehandler

    def format(self, record: LogRecord):
        if "root" in record.name:
            record.name = "source.shake"
        elif record.name.startswith("Extensions."):
            packages = record.name.split(".")
            record.name = packages[2] + "." + packages[-2]
        formatter = (
            (
                # logging.Formatter(
                #     "[{asctime}] [{levelname:<8}] {name:<21}: {message}",
                #     "%Y-%m-%d - %H:%M:%S",
                #     style="{"
                Logger(
                    "[{asctime}] [{levelname:<8}] {name:<21}: {message} [{filename}:{lineno}]",
                    "%Y-%m-%d - %H:%M:%S",
                    style="{",
                )
            )
            if self.filehandler
            else self.FORMATS.get(record.levelno) or self.FORMATS[DEBUG]
        )
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f"\x1b[31m{text}\x1b[0m "

        output = formatter.format(record)
        output = output.replace("\x1b[35msource.shake", "\x1b[33msource.shake")

        if self.filehandler:
            for x in [
                "\x1b[30;1m",
                "\033[1m",
                "\x1b[0m",
                "\x1b[40;1m",
                "\x1b[34;1m",
                "\x1b[33;1m",
                "\x1b[31m",
                "\x1b[41m",
                "\x1b[35m",
                "\x1b[33m",
            ]:
                output = output.replace(x, "")

        record.exc_text = None
        return output


def handler(
    file: Optional[bool] = False,
    stream: Optional[bool] = False,
    filepath: Optional[str] = "",
    filters: Optional[Tuple[Filter]] = None,
):
    stream_handler = file_handler = None
    if file:
        if not filepath:
            raise AttributeError(
                "For a FileHandler the `filepath` argument needs to be passed"
            )
        file_handler = FileHandler(filename=filepath, encoding="utf-8", mode="w")
        file_handler.setFormatter(Formatter(filehandler=True))
        if filters:
            for filter in filters:
                file_handler.addFilter(filter)

    if stream:
        stream_handler = StreamHandler()
        stream_handler.setLevel(INFO)
        stream_handler.setFormatter(Formatter())
        if filters:
            for filter in filters:
                stream_handler.addFilter(filter)
    return file_handler, stream_handler
