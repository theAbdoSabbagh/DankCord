from src.DankCord import Client
from src.DankCord import Config
from pyloggor import pyloggor

client = Client(
    Config("ODU4MzQ3NzExNzk4NTc1MTE0.GUpvnX.CaYu1wv-BoPqnElrOMEfRV1ltCCAXSu5b178yo", 1043808045450412044),
    pyloggor(
        show_file=False,
        show_topic=False,
        show_symbol=False,
        show_time=False,
        title_level=True,
        level_adjustment_space=9,
    ),
)
