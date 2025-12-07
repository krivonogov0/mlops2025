import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class Color:
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class MonitoringLogger:
    def __init__(self, log_file: str, metrics_file: str, console_colors: bool = True):
        self.log_file = Path(log_file)
        self.metrics_file = Path(metrics_file)
        self.console_colors = console_colors
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("monitor")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        time_fmt = "%H:%M:%S"

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._get_console_formatter(time_fmt))
        self.logger.addHandler(console_handler)

        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)-8s → %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        self.logger.addHandler(file_handler)

    def _colorize(self, text: str, color: str) -> str:
        if self.console_colors:
            return f"{color}{text}{Color.RESET}"
        return text

    def _get_console_formatter(self, time_fmt: str):
        class CustomFormatter(logging.Formatter):
            def __init__(self, outer):
                super().__init__()
                self.outer = outer

            def format(self, record):
                time_str = datetime.fromtimestamp(record.created).strftime(time_fmt)
                level = record.levelname

                if level == "INFO":
                    prefix = self.outer._colorize("🟢 INFO ", Color.GREEN + Color.BOLD)
                elif level == "WARNING":
                    prefix = self.outer._colorize("🟡 WARN ", Color.YELLOW + Color.BOLD)
                elif level == "ERROR":
                    prefix = self.outer._colorize("🔴 ERROR", Color.RED + Color.BOLD)
                else:
                    prefix = f"{level[:4]:<6}"

                return f"{time_str} | {prefix} | {record.getMessage()}"

        return CustomFormatter(self)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def alert(self, level: str, message: str):
        emoji_map = {"green": "🟢", "yellow": "🟡", "red": "🔥"}
        color_map = {
            "green": Color.GREEN + Color.BOLD,
            "yellow": Color.YELLOW + Color.BOLD,
            "red": Color.RED + Color.BOLD,
        }
        emoji = emoji_map.get(level, "❓")
        color = color_map.get(level, "")
        display_msg = f"{emoji} [{level.upper()}]: {message}"

        if self.console_colors:
            display_msg = f"{color}{display_msg}{Color.RESET}"

        self.logger.info(display_msg)
    
    def log(self, level: str, message: str):
        getattr(self.logger, level.lower())(message)

    def log_metrics(self, metrics: Dict[str, Any]):
        with open(self.metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(metrics, ensure_ascii=False, default=str) + "\n")
