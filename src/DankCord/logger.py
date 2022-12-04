from rich import print

from .Objects import Bot


class Logger:
    def __init__(self) -> None:
        self.pipe = "[bold black]|[/]"
        self.header = "[bold green]Dank[/][bold blue]Cord[/]"

        self.bot = ""
        self._bot_info = ""

    def set_dets(self, bot: dict[str, str]):
        self.bot = Bot(bot)
        self._bot_info = f"{self.pipe} [bold]{self.bot.bot}[/] {self.pipe}"

    def ws(self, text: str):
        print(f"{self.header} {self._bot_info} [bold grey37]Websocket:[/] {text}")

    def bootup(self, text: str, booted: bool = False):
        print(
            f"{self.header} {self._bot_info} [bold grey37]{'Booted' if booted else 'Booting'} up:[/] {text}"
        )

    def error(self, text: str):
        print(f"{self.header} {self._bot_info} [bold red]Error:[/] {text}")

    def success(self, text: str):
        print(f"{self.header} {self._bot_info} [bold green]Success:[/] {text}")

    def ratelimit(self, retry_after: int, command_name: str = None):
        message = (
            f"[bold red]Ratelimit:[/] Trying again in {retry_after} seconds."
            if command_name is None
            else f"[bold red]Ratelimit with {command_name}:[/] Trying again in {retry_after} seconds."
        )
        print(f"{self.header} {self._bot_info} {message}")
