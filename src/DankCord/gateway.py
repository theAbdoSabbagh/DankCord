import threading, time, orjson

from rich import print
from typing import Optional
from pyloggor import pyloggor
from websocket import create_connection

from .exceptions import InvalidToken
from .Objects import Cache, Config


class GatewayInternal:
    def __init__(self) -> None:
        self.s = 0
        self.resume_gateway_url = ""


class Gateway:
    def __init__(self, config: Config, logger: pyloggor) -> None:
        logger.log(level="Debug", msg="Booting up gateway instance.")
        self.token = config.token
        self.logger = logger

        self.channel_id = config.channel_id
        self.dm_mode = config.dm_mode

        self.session_id: Optional[str] = None
        self.user_id: Optional[int] = None
        self.guild_id: Optional[int] = None

        self.internal: GatewayInternal = GatewayInternal()
        self.cache: Cache = Cache()
        self.pause = False

        self.__boot_ws()

    def heartbeat(self):
        self.logger.log(level="Debug", msg="Booted up discord heartbeat loop.")
        self.pause = False
        while True:
            if not self.pause:
                time.sleep(self.heartbeat_interval)
                self.ws.send(orjson.dumps({"op": 1, "d": None}))

    def recv_handler(self):
        try:
            event = self.ws.recv()
            data = orjson.loads(event)
            return data
        except:
            return False

    def __boot_ws(self):
        start = time.perf_counter()
        self.logger.log(level="Debug", msg="Booting up websocket client.")
        ws = create_connection("wss://gateway.discord.gg/?v=9&encoding=json")
        self.ws = ws

        hello = self.recv_handler()
        if not hello:
            self.logger.log(level="Critical", msg="Discord websocket client failed to boot.")
            return False

        self.heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000
        self.logger.log(level="Debug", msg="Received gateway hello event.")

        self.ws.send(orjson.dumps({"op": 1, "d": None}))
        heartbeat_init = self.recv_handler()
        if not heartbeat_init:
            self.logger.log(level="Critical", msg="Discord heartbeat loop failed to boot.")
            return False

        if heartbeat_init["op"] == 11:
            pass
        elif heartbeat_init["op"] == 1:
            self.ws.send(orjson.dumps({"op": 1, "d": None}))
            heartbeat_init_2 = self.recv_handler()
            if not heartbeat_init_2:
                self.logger.log(level="Critical", msg="Discord heartbeat loop failed to boot.")
                return False
            if heartbeat_init_2["op"] != 11:
                self.logger.log(level="Critical", msg="Unhandled OP response while booting discord heartbeat loop.")
                return False
        else:
            self.logger.log(level="Critical", msg="Unhandled OP response while booting discord heartbeat loop.")
            return False

        threading.Thread(target=self.heartbeat).start()

        ws.send(
            orjson.dumps(
                {
                    "op": 2,
                    "d": {
                        "token": self.token,
                        "properties": {
                            "$os": "windows",
                            "$browser": "Discord",
                            "$device": "desktop",
                        },
                    },
                }
            )
        )

        identify = self.recv_handler()
        if not identify:
            raise InvalidToken("Invalid Discord account token used.") # type: ignore

        if identify["op"] != 0:
            self.logger.log(
                level="UNHANDLED DEBUG",
                msg="Unhandled case, send this to the developers.",
                extras={"identify_response": identify},
            )
            return False

        self.internal.s = identify["s"]

        end = time.perf_counter()

        if not self.dm_mode:
            self.logger.log(level="Debug", msg="Caching guild ID")
            for guild in identify["d"]["guilds"]:
                for channel in guild["channels"]:
                    if int(channel["id"]) == int(self.channel_id):
                        self.logger.log(level="Debug", msg="Found guild ID.")
                        self.guild_id = guild["id"]
                        break

        self.user_id = int(identify["d"]["user"]["id"])
        self.session_id = identify["d"]["session_id"]
        self.internal.resume_gateway_url = identify["d"]["resume_gateway_url"]

        thread = threading.Thread(target=self._events_listener)
        thread.daemon = True
        thread.start()
        self.logger.log(level="Info", msg=f"Connected to gateway in {round(end - start, 3)} seconds.")

    def reconnect_ws(self):
        self.logger.log(level="Info", msg="Reconnecting websocket client.")
        ws = create_connection(self.internal.resume_gateway_url)
        self.ws = ws
        self.ws.send(
            orjson.dumps({"op": 6, "d": {"token": self.token, "session_id": self.session_id, "seq": self.internal.s}})
        )

        thread = threading.Thread(target=self._events_listener)
        thread.daemon = True
        thread.start()
        self.pause = False

    def _events_listener(self):
        self.logger.log(level="Debug", msg="Events listener is now listening.")
        while True:
            event = self.recv_handler()
            if not event:
                continue
            
            try:
                if event["op"] == 0:
                    self.internal.s = event["s"]

                elif event["op"] == 7 or (event["op"] == 9 and event["d"]):
                    self.reconnect_ws()
                    return
                elif event["op"] == 1:
                    self.ws.send(orjson.dumps({"op": 1, "d": None}))
                    continue
                elif event["op"] == 9 and not event["d"]:
                    self.pause = True
                    self.__boot_ws()
                    return

                if not event["d"]:
                    continue
                if event["t"] == "MESSAGE_ACK":
                    continue

                if event["t"] not in ("MESSAGE_CREATE", "MESSAGE_UPDATE", "INTERACTION_CREATE", "INTERACTION_SUCCESS"):
                    continue
                
                if event["t"] == "INTERACTION_CREATE":
                    self.cache.interaction_create.append(event["d"]["nonce"])
                elif event["t"] == "INTERACTION_SUCCESS":
                    self.cache.interaction_success.append(event["d"]["nonce"])
                elif event["t"] == "MESSAGE_CREATE":
                    try:
                        self.cache.message_create[event["d"]["nonce"]] = event["d"]
                        self.cache.nonce_message_map[event["d"]["nonce"]] = event["d"]["id"]
                    except:
                        pass
                elif event["t"] == "MESSAGE_UPDATE":
                    if event["d"]["id"] not in self.cache.message_updates:
                        self.cache.message_updates[event["d"]["id"]] = []
                    self.cache.message_updates[event["d"]["id"]].append(event["d"])
                    self.cache.raw_message_updates.append(event["d"])
                else:
                    print("----------------- DEBUG START -----------------")
                    print(event)
                    print("----------------- DEBUG END -----------------")
            except Exception as e:
                self.logger.log(level="Error", msg=f"_events_listener function in gateway.py: {e}.")