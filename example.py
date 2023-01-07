from typing import Optional

from DankCord import Client, Config
from DankCord.objects import Message
from pyloggor import pyloggor

bot = Client(
    Config("TOKEN", 00000000000), # Second argument is channel ID, must be int
    pyloggor(
        show_file=False,
        show_topic=False,
        show_symbol=False,
        show_time=False,
        title_level=True,
        level_adjustment_space=9,
    ),
)
message: Optional[Message] = bot.core.fish()
message: Optional[Message] = bot.core.beg()
message: Optional[Message] = bot.core.hunt()
message: Optional[Message] = bot.run_command(name = "hunt")
message: Optional[Message] = bot.run_sub_command(name = "advancements", sub_name = "prestige")