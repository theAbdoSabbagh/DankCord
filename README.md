![DankCord](https://raw.githubusercontent.com/Sxvxgee/DankCord/master/assets/DankCord.png)

[![Discord Server](https://discord.com/api/guilds/1046759026807013376/embed.png)](https://discord.gg/XaQ6FAP3sm/)
[![PyPi version](https://img.shields.io/pypi/v/DankCord.svg)](https://pypi.org/user/Sxvxge/)
[![PyPI download month](https://img.shields.io/pypi/dm/DankCord.svg)](https://pypi.org/user/Sxvxge/)

# DankCord - The first python library for Dank Memer selfbots!
My vision for this library is to be able to help people create their very own selfbots related to Dank Memer, and even create autofarms based on this library, instead of having to use other libraries such as `discord.py-self` as others can be slow, use lots of memory, and the user would have to code many things on their own from scratch.

# Installing
```sh
# linux/macOS
python3 -m pip install -U DankCord

# windows
pip install -U DankCord
```
To install the Github version, do the following:
```sh
$ git clone https://github.com/Sxvxgee/DankCord
$ cd DankCord
$ python3 -m pip install -U .
```
# Quick Example
```py
from typing import Optional

from DankCord import Client, Config
from DankCord.Objects import Message
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
message: Optional[Message] = bot.run_command(name = "settings")
message: Optional[Message] = bot.run_sub_command(name = "advancements", sub_name = "prestige")
```

# Links
- [Discord](https://discord.gg/XaQ6FAP3sm)
- [Trello board](https://trello.com/b/0M9SDJH6/dankcord)
- Documentation: coming soon.

# Special thanks
- [ThePrivatePanda](https://github.com/ThePrivatePanda): An ex-maintainer of the project.
- All our other contributors, DankCord wouldn't have been what it is today without them.
