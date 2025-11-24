from rich.console import Console
from rich.theme import Theme
import datetime

# Define a custom theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "debug": "green",
    "critical": "bold magenta",
    "timestamp": "bold grey50"
})

console = Console(theme=custom_theme)

class PrettyLogger:
    def __init__(self, name):
        self.name = name

    def _log(self, level, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[timestamp]{timestamp}[/timestamp] [{level}]{level.upper()}[/] {message}"
        console.print(log_message)

    def debug(self, message):
        self._log("debug", message)

    def info(self, message):
        self._log("info", message)

    def warning(self, message):
        self._log("warning", message)

    def error(self, message):
        self._log("error", message)

    def critical(self, message):
        self._log("critical", message)

logger = PrettyLogger("MyLogger")

# Example usage
#if __name__ == "__main__":
#    logger.debug("This is a debug message.")
#    logger.info("This is an info message.")
#    logger.warning("This is a warning message.")
#    logger.error("This is an error message.")
#    logger.critical("This is a critical message.")