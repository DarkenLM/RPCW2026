from __future__ import annotations
from typing import Protocol, List, Any
from datetime import datetime

class LoggerFormatter(Protocol):
    def __call__(
        self,  # This won't be part of the function signature
        _self: 'Logger',
        level: int,
        timestamp: datetime,
        args: List[Any]
    ) -> str:
        ...

_DefaultLoggerFormatter: LoggerFormatter = lambda self, level, timestamp, args: \
    f"{self._COLOR_NAME}[{self.name}]{self._COLOR_RESET} {self.colors[level]}" \
        + f"[{self.levelnames[level]}]".ljust(self._levelnameSize + 2, ' ') \
        + f" {timestamp.strftime('[%Y-%m-%dT%H:%M:%S]')} " \
        + " ".join(args) # pyright: ignore[reportAssignmentType]

class Logger:
    LOG_DEBUG = 0b0001
    LOG_INFO  = 0b0010
    LOG_WARN  = 0b0100
    LOG_ERROR = 0b1000
    _LOG_LEVEL_DEFAULT = 0
    _LOG_DEFAULT_LEVELS = LOG_INFO | LOG_WARN | LOG_ERROR

    _LOG_DEFAULT_COLORS = {
        _LOG_LEVEL_DEFAULT: "\x1b[37m",
        LOG_DEBUG: "\x1b[35m",
        LOG_INFO: "\x1b[34m",
        LOG_WARN: "\x1b[33m",
        LOG_ERROR: "\x1b[31m",
    }
    _LOG_DEFAULT_LEVEL_NAMES = {
        _LOG_LEVEL_DEFAULT: "LOG",
        LOG_DEBUG: "DEBUG",
        LOG_INFO:  "INFO",
        LOG_WARN:  "WARN",
        LOG_ERROR: "ERROR",
    }
    _COLOR_NAME = "\x1b[36m"
    _COLOR_RESET = "\x1b[0m"

    def __init__(
        self, 
        name, 
        levels = _LOG_DEFAULT_LEVELS, 
        levelnames = _LOG_DEFAULT_LEVEL_NAMES,
        colors = _LOG_DEFAULT_COLORS, 
        formatter: LoggerFormatter = _DefaultLoggerFormatter
    ):
        self.name = name
        self.levels = levels
        self.levelnames = levelnames
        self.colors = colors
        self.formatter = formatter

        self._levelnameSize = max(map(lambda n: len(n), self.levelnames.values()))

    def _log(self, level, args):
        if (self.levels & level != level): return 
        s = self.formatter(self, level, datetime.now(), args)
        print(s, Logger._COLOR_RESET)

    def debug(self, *args): self._log(Logger.LOG_DEBUG, args)
    def info(self, *args): self._log(Logger.LOG_INFO, args)
    def warn(self, *args): self._log(Logger.LOG_WARN, args)
    def error(self, *args): self._log(Logger.LOG_ERROR, args)
    def log(self, *args): self._log(Logger._LOG_LEVEL_DEFAULT, args)

    def setLevel(self, level: int, active: bool):
        if (active): self.levels |= level
        else: self.levels &= ~level

logger = Logger("root")