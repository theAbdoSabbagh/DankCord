import random
import threading
import time
from typing import Optional

import orjson
from rich import print
from websocket import create_connection

from .exceptions import InvalidToken
from .logger import Logger


class Gateway:
    def __init__(self, token: str, channel_id: str, logger: Logger) -> None:
        self.token = token
        self.logger = logger
        self.channel_id = channel_id

        self.session_id: Optional[str] = None
        self.user_id: Optional[int] = None
        self.guild_id: Optional[int] = None

        self.logger.bootup(f"Local Discord signal client.")

        self.__boot_ws()

    def heartbeat(self):
        while True:
            time.sleep(self.heartbeat_interval)
            self.ws.send(orjson.dumps({"op": 1, "d": None}))

    def __boot_ws(self):
        start = time.time()
        self.logger.bootup("Discord websocket client.")
        ws = create_connection("wss://gateway.discord.gg/?v=9&encoding=json")

        hello = orjson.loads(ws.recv())

        self.ws = ws
        self.heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000
        self.logger.bootup("Discord heartbeat client.")

        jitter_heartbeat = self.heartbeat_interval * random.uniform(0, 0.1)

        time.sleep(jitter_heartbeat)
        ws.send(orjson.dumps({"op": 1, "d": None}))
        response = orjson.loads(ws.recv())

        if response["op"] != 11:
            self.logger.error("Discord heartbeat client failed to boot.")
            return False

        threading.Thread(target=self.heartbeat).start()
        self.logger.bootup("Discord heartbeat client.", booted=True)

        ws.send(
            orjson.dumps(
                {
                    "op": 2,
                    "d": {
                        "token": self.token,
                        "intents": 38408,
                        "properties": {
                            "$os": "windows",
                            "$browser": "Discord",
                            "$device": "desktop",
                        },
                    },
                }
            )
        )

        identify = ws.recv()
        if not identify:
            raise InvalidToken("Invalid Discord account token used.")

        end = time.time()
        identify_json = orjson.loads(identify)

        for guild in identify_json["d"]["guilds"]:
            for channel in guild["channels"]:
                if channel["id"] == self.channel_id:
                    self.guild_id = guild["id"]
                    break

        self.user_id = int(identify_json["d"]["user"]["id"])
        self.session_id = identify_json["d"]["session_id"]

        self.logger.set_dets(identify_json)
        self.logger.ws(f"Logged into bot in {round(end - start, 2)} seconds.")
