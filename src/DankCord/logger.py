from rich import print
from .Objects import Bot

class Logger:
  def __init__(self, bot : Bot = None) -> None:
    self.bot = Bot(bot) if bot is not None else None
    self.header = "[bold green]Dank[/][bold blue]Cord[/]"
    self.barrier = "[bold black]|[/]"
    self._bot_info = f"{self.barrier} [bold]{self.bot.bot}[/] {self.barrier}" if self.bot is not None else self.barrier

  def ws(self, /, text : str):
    print(f"{self.header} {self._bot_info} [bold grey37]Websocket:[/] {text}")

  def bootup(self, /, text : str, booted : bool = False):
    print(f"{self.header} {self._bot_info} [bold grey37]{'Booted' if booted else 'Booting'} up:[/] {text}")
  
  def error(self, /, text : str):
    print(f"{self.header} {self._bot_info} [bold red]Error:[/] {text}")
  
  def success(self, /, text : str):
    print(f"{self.header} {self._bot_info} [bold green]Success:[/] {text}")