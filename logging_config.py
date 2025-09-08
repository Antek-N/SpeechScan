"""
Unified configuration of color-aware UTC logging for console and file.

Global logging configuration in Python: colorful logs in the console (ANSI, if supported),
timestamps in UTC format, and optional file output. The module automatically detects the
environment (VS Code, PyCharm, Jupyter, CI, Windows/Unix) and decides whether to enable
colors. This ensures consistent, readable logs with a unified format across the entire project.

Usage (once at startup):
    from logging_config import configure_logging, add_file_logging
    configure_logging()          # colorful logs to stderr (MUST be called first)
    add_file_logging("app.log")  # optional: log to file (UTC, no colors)

Then:
    import logging
    log = logging.getLogger(__name__)
    log.info("Sample info")
    log.error("Sample error")

Parameters:
- configure_logging(
      level=logging.DEBUG,    # minimum log level
      stream=sys.stderr,      # where to write logs (e.g., sys.stdout)
      format_string="...",    # message format (default: ISO-8601 UTC)
      date_format="...",      # date format
      replace_handlers=False, # True → removes old handlers and sets new ones
      capture_warnings=True   # redirects warnings module output to logs
  )

- add_file_logging(
      path,                   # path to log file
      level=logging.DEBUG,    # minimum log level for file
      format_string="...",    # message format (UTC)
      date_format="...",      # date format
      encoding="utf-8"        # file encoding
  )

Important:
- Always call configure_logging() first, then optionally add_file_logging().
- Call both functions only once. Afterward, use log = logging.getLogger(__name__).
- Colors: `FORCE_COLOR=1` enforces colors, `NO_COLOR=1` disables them
  (set as environment variables before running the program).
"""
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import IO, Optional

__all__ = ["configure_logging", "add_file_logging"]


# mapping of logging levels to ANSI codes (terminal colors)
# RESET is needed so that after each message the default color is restored
COLORS = {
    "DEBUG": "\033[90m",  # gray
    "INFO": "\033[32m",  # green
    "WARNING": "\033[93m",  # yellow
    "ERROR": "\033[91m",  # red
    "CRITICAL": "\033[97;41m",  # white text on red background
    "RESET": "\033[0m",  # reset to default terminal color
}


# ------------------------ Layer: environment/color detection ------------------------


@dataclass(frozen=True)
class ColorSupport:
    """
    Represents whether ANSI color output is supported in the current environment.

    Attributes:
        supported (bool): True if ANSI colors are supported, False otherwise.
        reason (Optional[str]): Explanation why colors are not supported (if applicable).
        env_hint (Optional[str]): Environment hint to provide user-specific tips (e.g. 'vscode', 'pycharm').
    """
    supported: bool
    reason: Optional[str] = None
    env_hint: Optional[str] = None


class ColorEnv:
    """
    Detects environment characteristics related to color/ANSI support
    and provides methods to enable or disable ANSI colors in different terminals.
    """
    _WINDOWS_ANSI_ENABLED = False  # flag: whether ANSI support was enabled on Windows (via colorama)
    _COLOR_HINT_SHOWN = False  # flag: so that color hint is shown only once

    @staticmethod
    def is_ci() -> bool:
        """
        Detects if the current process is running inside a CI environment.

        :return: True if running in a known CI system, False otherwise.
        """
        return (
            os.environ.get("CI") == "1"  # compatibility with tools that set CI=1
            or any(
                os.environ.get(env_var)
                for env_var in (
                    "GITHUB_ACTIONS",
                    "GITLAB_CI",
                    "TF_BUILD",
                    "TEAMCITY_VERSION",
                    "BUILDKITE",
                    "TRAVIS",
                    "CIRCLECI",
                    "APPVEYOR",
                    "DRONE",
                    "JENKINS_URL",
                )  # list of the most common CI environment variables
            )
        )

    @staticmethod
    def is_vscode() -> bool:
        """
        Detects if the process is running inside VS Code's Integrated Terminal or Debug Console.

        :return: True if running in VS Code, False otherwise.
        """
        return bool(
            os.environ.get("TERM_PROGRAM") == "vscode"  # VS Code Integrated Terminal sets TERM_PROGRAM=vscode
            or os.environ.get("VSCODE_PID")  # debug/run without terminal may only have VSCODE_PID
        )

    @staticmethod
    def is_pycharm() -> bool:
        """
        Detects if the process is running inside the PyCharm IDE.

        :return: True if running in PyCharm, False otherwise.
        """
        return bool(
            os.environ.get("PYCHARM_HOSTED")
        )  # PyCharm sets PYCHARM_HOSTED when process is run “inside” IDE

    @staticmethod
    def is_windows_terminal() -> bool:
        """
        Detects if the process is running in Windows Terminal or ConEmu.

        :return: True if running in Windows Terminal or ConEmu, False otherwise.
        """
        return bool(
            os.environ.get("WT_SESSION")  # Windows Terminal sets WT_SESSION — supports ANSI
            or os.environ.get("ConEmuPID")  # ConEmu/CMder can emulate colors, so we also treat them as supported
        )

    @staticmethod
    def is_jupyter() -> bool:
        """
        Detects if the process is running inside a Jupyter or Spyder kernel.

        :return: True if in Jupyter, False otherwise.
        """
        try:
            import ipykernel  # noqa: F401  # presence of ipykernel means we are in Jupyter/spyder-kernel – colors usually work
            return True  # if import succeeds, signal support
        except ImportError:
            return False  # no ipykernel > not Jupyter

    @classmethod
    def ensure_windows_ansi(cls) -> None:
        """
        Ensures that ANSI escape sequences are enabled in Windows consoles.
        Requires the `colorama` package.

        :return: None
        """
        # If ANSI is already enabled, or we are not on Windows — do nothing
        if cls._WINDOWS_ANSI_ENABLED or os.name != "nt":
            return

        try:
            # Try importing colorama library (required on Windows)
            import colorama  # type: ignore
        except ImportError:
            # If colorama not available — exit
            return

        colorama.just_fix_windows_console()  # Fix Windows console so it supports ANSI codes
        cls._WINDOWS_ANSI_ENABLED = True  # Internal flag — mark as already configured

    @staticmethod
    def stream_isatty(stream: IO[str]) -> bool:
        """
        Checks whether a given stream is connected to a TTY (interactive terminal).

        :param stream: The stream to check.
        :return: True if the stream is a TTY, False otherwise.
        """
        try:
            # Checks if `stream` object has `isatty` method
            # and whether it is callable, then returns its result.
            # `isatty()` -> True means the stream is a terminal (not e.g. file/pipe).
            return hasattr(stream, "isatty") and callable(stream.isatty) and stream.isatty()
        except (OSError, ValueError):
            # In case of errors (e.g. no access to terminal, closed stream) return False
            return False

    @classmethod
    def color_support_with_reason(cls, stream: IO[str]) -> ColorSupport:
        """
        Determines whether colors are supported in the current environment,
        including reasons and environment hints if disabled.

        :param stream: The output stream (e.g. sys.stderr).
        :return: A ColorSupport instance with the decision and explanation.
        """
        # If FORCE_COLOR is set -> always enforce colors
        if os.environ.get("FORCE_COLOR"):
            cls.ensure_windows_ansi()
            return ColorSupport(True)

        # If NO_COLOR is set -> completely disable colors
        if os.environ.get("NO_COLOR"):
            return ColorSupport(False, "NO_COLOR is set.", None)

        # Special environment: PyCharm
        if cls.is_pycharm():
            cls.ensure_windows_ansi()
            return ColorSupport(True, env_hint="pycharm")

        # Special environment: VS Code
        if cls.is_vscode():
            cls.ensure_windows_ansi()
            return ColorSupport(True, env_hint="vscode")

        # Windows Terminal or ConEmu -> try to enable ANSI
        if cls.is_windows_terminal():
            cls.ensure_windows_ansi()

        # In Jupyter environment we support colors by default
        if cls.is_jupyter():
            return ColorSupport(True, env_hint="jupyter")

        # If output is not a TTY (e.g. file, pipe, IDE without emulation) -> colors disabled
        if not cls.stream_isatty(stream):
            return ColorSupport(False, "Output is not a TTY (file/pipe/IDE wo/ emulation).", None)

        # Windows handling: if we have colorama -> OK, if not -> no support
        if os.name == "nt":
            cls.ensure_windows_ansi()
            return (
                ColorSupport(True)
                if cls._WINDOWS_ANSI_ENABLED
                else ColorSupport(False, "Windows without 'colorama'.", "windows")
            )

        # On Unix systems check TERM variable
        terminal_type = os.environ.get("TERM", "")
        if terminal_type in ("", "dumb"):
            # Empty TERM or "dumb" means no ANSI support
            return ColorSupport(False, f"TERM={terminal_type!r} does not support ANSI.", "unix")

        # In other cases assume colors are supported
        return ColorSupport(True)

    @classmethod
    def maybe_show_color_hint(cls, reason: Optional[str], env_hint: Optional[str]) -> None:
        """
        Optionally prints a hint to stderr explaining why colors are disabled
        and how to enable them, depending on the environment.

        :param reason: Reason why colors are disabled.
        :param env_hint: Environment hint (if available).
        :return: None
        """
        # Conditions when hint should not be shown:
        # - already shown (_COLOR_HINT_SHOWN),
        # - running in CI environment (where hints are useless),
        # - user did not enable hints (LOG_COLOR_HINT != "1").
        if cls._COLOR_HINT_SHOWN or cls.is_ci() or os.environ.get("LOG_COLOR_HINT") != "1":
            return

        # If no reason (reason=None), then no sense to show hint
        if not reason:
            return

        # Mark that hint was already shown — only once per process
        cls._COLOR_HINT_SHOWN = True

        # General tips independent of environment
        base_tips = [
            "- If redirecting to a file/pipeline: colors are intentionally disabled.",
            "- Remove the `NO_COLOR` variable if it's set.",
            "- You can force colors: `FORCE_COLOR=1`.",
        ]

        # Additional, environment-specific tips depending on detected env
        env_tips = {
            "pycharm": ["- PyCharm: enable **Run → Emulate terminal in output console**."],
            "vscode": [
                "- VS Code: use the **Integrated Terminal** (View → Terminal),",
                "  or set `FORCE_COLOR=1` in your Debug Configuration.",
            ],
            "windows": ["- Windows: `pip install colorama` or run in Windows Terminal."],
            "unix": [
                "- Linux/macOS: ensure `TERM` is something like `xterm-256color`.",
                "- In Docker, run with a TTY: `docker run -it ...`.",
            ],
            "jupyter": ["- Jupyter: colors usually work; to disable set `NO_COLOR=1`."],
            None: [
                "- Windows: consider **Windows Terminal** or `pip install colorama`.",
                "- VS Code/PyCharm: run via the **Integrated/Emulated Terminal**.",
                "- Docker: add `-t` (pseudo-TTY).",
            ],
        }

        # Pick tips list depending on env_hint (or default None)
        tips = env_tips.get(env_hint, env_tips[None])

        # Build final message — reason for disabling and tips how to enable colors
        message = (
            "[log-color] Colors are disabled: "
            f"{reason}  How to enable them:\n  " + "\n  ".join(tips + base_tips)
            + "\n  (Silence tips: LOG_COLOR_HINT=0 / off by default)"
        )

        try:
            # Print message to stderr
            print(message, file=sys.stderr)
        except (OSError, ValueError):
            # If stderr not available -> ignore error
            pass


# ----------------------------- Layer: formatters/handlers -----------------------------


class UtcFormatter(logging.Formatter):
    """
    Formatter that enforces UTC timestamps for log records.
    """
    converter = time.gmtime


class ColoredFormatter(UtcFormatter):
    """
    A log formatter that applies ANSI color codes to messages based on log level.

    Extends UtcFormatter to add colorization when enabled.
    """
    def __init__(self, format_string: str, date_format: Optional[str], use_color: bool) -> None:
        # Inherits from UtcFormatter and additionally handles colors
        super().__init__(fmt=format_string, datefmt=date_format)
        self.use_color = use_color  # flag, whether to use colors

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a log record, optionally adding ANSI color sequences.

        :param record: The log record to format.
        :return: The formatted log message string.
        """
        # First, format normally
        message = super().format(record)

        if not self.use_color:
            # If colors disabled -> return plain text
            return message

        # Pick color based on log level
        color = COLORS.get(record.levelname, COLORS["RESET"])

        # Add ANSI sequence before and reset after message
        return f"{color}{message}{COLORS['RESET']}"


class HandlerFactory:
    """
    Factory for creating logging handlers with appropriate formatters
    (stream handlers with optional colors, or file handlers without colors).
    """
    @staticmethod
    def stream_handler(stream: IO[str], fmt: str, date_format: str) -> logging.Handler:
        """
        Creates a logging.StreamHandler with color support if available.

        :param stream: The target output stream.
        :param fmt: Log message format string.
        :param date_format: Date/time format string.
        :return: Configured logging handler.
        """
        # Creates handler for logging to given stream (e.g. stderr)
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.NOTSET)  # allows all levels to pass

        # Check if colors can be used in this stream
        support = ColorEnv.color_support_with_reason(stream)
        if not support.supported:
            # If colors unavailable -> maybe show hint
            ColorEnv.maybe_show_color_hint(support.reason, support.env_hint)

        # Set formatter: colored if environment supports
        handler.setFormatter(
            ColoredFormatter(format_string=fmt, date_format=date_format, use_color=support.supported)
        )
        return handler

    @staticmethod
    def file_handler(path: str, fmt: str, date_format: str, encoding: str = "utf-8") -> logging.Handler:
        """
        Creates a logging.FileHandler that writes logs to a file using UTC timestamps.

        :param path: Path to the log file.
        :param fmt: Log message format string.
        :param date_format: Date/time format string.
        :param encoding: File encoding (default UTF-8).
        :return: Configured logging handler.
        """
        # Creates handler for logging to file (without colors)
        absolute_path = os.path.abspath(path)
        handler = logging.FileHandler(absolute_path, encoding=encoding)
        handler.setLevel(logging.NOTSET)

        # Use formatter with UTC time (no colors, since file)
        handler.setFormatter(UtcFormatter(fmt=fmt, datefmt=date_format))
        return handler


# ------------------------------ Layer: configuration ---------------------------------


class LoggingConfigurator:
    """
    Provides high-level configuration methods for setting up logging
    with optional color support for console and file handlers.
    """
    @staticmethod
    def configure(
        level: int = logging.DEBUG,
        stream: IO[str] = sys.stderr,
        format_string: str = "%(asctime)s.%(msecs)03dZ [%(levelname)s] %(name)s: %(message)s",
        date_format: str = "%Y-%m-%dT%H:%M:%S",
        *,
        replace_handlers: bool = False,
        capture_warnings: bool = True,
    ) -> None:
        """
        Configures global logging with colorized console output.

        :param level: Minimum logging level (default DEBUG).
        :param stream: Stream to log to (default sys.stderr).
        :param format_string: Log message format string.
        :param date_format: Date/time format string.
        :param replace_handlers: If True, removes existing handlers first.
        :param capture_warnings: If True, redirects warnings to logging.
        :return: None
        """
        root = logging.getLogger()  # main application logger

        if replace_handlers:
            # replace_handlers=True -> start with clean config (no old handlers/flags)
            for handler in root.handlers[:]:
                root.removeHandler(handler)

            # Clear flag that configuration was already set
            if hasattr(root, "_colored_logging_configured"):
                delattr(root, "_colored_logging_configured")

        # If logger already configured and replace_handlers not forced
        if getattr(root, "_colored_logging_configured", False) and not replace_handlers:
            if capture_warnings:
                # capture standard warnings and direct them to logs
                logging.captureWarnings(True)
            return  # done, change nothing more

        # Set global logging level
        root.setLevel(level)

        # Add stream handler (e.g. stderr) with formatter
        root.addHandler(HandlerFactory.stream_handler(stream, format_string, date_format))

        # Flag — mark that configuration was done
        root._colored_logging_configured = True  # type: ignore[attr-defined]

        if capture_warnings:
            # capture standard warnings and direct them to logs
            logging.captureWarnings(True)

    @staticmethod
    def add_file_logging(
        path: str,
        level: int = logging.DEBUG,
        format_string: str = "%(asctime)s.%(msecs)03dZ [%(levelname)s] %(name)s: %(message)s",
        date_format: str = "%Y-%m-%dT%H:%M:%S",
        encoding: str = "utf-8",
    ) -> None:
        """
        Adds a file handler to the global logger, writing logs in UTC.

        :param path: Path to the log file.
        :param level: Minimum logging level (default DEBUG).
        :param format_string: Log message format string.
        :param date_format: Date/time format string.
        :param encoding: File encoding (default UTF-8).
        :return: None
        """
        root = logging.getLogger()  # main application logger
        absolute_path = os.path.abspath(path)  # file path

        # check if logger already has handler for the same file
        for handler in root.handlers:
            if isinstance(handler, logging.FileHandler) and getattr(handler, "baseFilename", None) == absolute_path:
                # if file already attached, possibly raise logging level
                if root.level > level:
                    root.setLevel(level)
                return  # do not add another handler

        # add new file handler with UTC formatter
        root.addHandler(
            HandlerFactory.file_handler(absolute_path, format_string, date_format, encoding)
        )

        # ensure global logging level is not higher than given
        if root.level > level:
            root.setLevel(level)


# -------------------------------------- API ------------------------------------------


def configure_logging(
    level: int = logging.DEBUG,
    stream: IO[str] = sys.stderr,
    format_string: str = "%(asctime)s.%(msecs)03dZ [%(levelname)s] %(name)s: %(message)s",
    date_format: str = "%Y-%m-%dT%H:%M:%S",
    *,
    replace_handlers: bool = False,
    capture_warnings: bool = True,
) -> None:
    """
    Public API to configure global logging with colorized console output.

    :param level: Minimum logging level (default DEBUG).
    :param stream: Stream to log to (default sys.stderr).
    :param format_string: Log message format string.
    :param date_format: Date/time format string.
    :param replace_handlers: If True, removes existing handlers first.
    :param capture_warnings: If True, redirects warnings to logging.
    :return: None
    """
    LoggingConfigurator.configure(
        level=level,
        stream=stream,
        format_string=format_string,
        date_format=date_format,
        replace_handlers=replace_handlers,
        capture_warnings=capture_warnings,
    )


def add_file_logging(
    path: str,
    level: int = logging.DEBUG,
    format_string: str = "%(asctime)s.%(msecs)03dZ [%(levelname)s] %(name)s: %(message)s",  # Default - ISO-8601
    date_format: str = "%Y-%m-%dT%H:%M:%S",
    encoding: str = "utf-8",
) -> None:
    """
    Public API to add file logging to the global logger.

    :param path: Path to the log file.
    :param level: Minimum logging level (default DEBUG).
    :param format_string: Log message format string.
    :param date_format: Date/time format string.
    :param encoding: File encoding (default UTF-8).
    :return: None
    """
    LoggingConfigurator.add_file_logging(
        path=path,
        level=level,
        format_string=format_string,
        date_format=date_format,
        encoding=encoding,
    )
