from src.DankCord import Client, Config
from pyloggor import pyloggor

client = Client(
    Config("TOKEN", 00000000000),
    pyloggor(
        show_file=False,
        show_topic=False,
        show_symbol=False,
        show_time=False,
        title_level=True,
        level_adjustment_space=9,
    ),
)
