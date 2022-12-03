import threading, random, time
import orjson as json

from rich import print
from typing import Optional, Union
from websocket import create_connection

from .exceptions import InvalidToken
from .logger import Logger

class Gateway:
  def __init__(self, token : str):
    self.session_id: str = None
    self.user_id: int = None
    self.token = token
    self.logger = Logger()
    self.logger.bootup(f"Local Discord signal client.")

    self.__boot_ws()

  def heartbeat(self):
    while True:
      time.sleep(self.heartbeat_interval)
      self.ws.send(json.dumps({"op": 1, "d": None}))

  def __boot_ws(self):
    start = time.time()
    self.logger.bootup("Discord websocket client.")
    ws = create_connection("wss://gateway.discord.gg/?v=9&encoding=json")

    hello = json.loads(ws.recv())

    self.ws = ws
    self.heartbeat_interval = hello["d"]["heartbeat_interval"]/1000
    self.logger.bootup("Discord heartbeat client.")

    jitter_heartbeat = self.heartbeat_interval * random.uniform(0, 0.1)

    time.sleep(jitter_heartbeat)
    ws.send(json.dumps({"op": 1, "d": None}))
    response = json.loads(ws.recv())

    if response["op"] != 11:
      print("Discord heartbeat client failed to boot.")
      return False

    thread = threading.Thread(target = self.heartbeat).start()
    self.logger.bootup("Discord heartbeat client.", booted = True)

    ws.send(json.dumps(
      {
        "op": 2,
        "d": {
          "token": self.token,
          "intents": 38408, ## Use 37377 if this doesn't work
          "properties": {
            "$os": "windows",
            "$browser": "Discord",
            "$device": "desktop"
          }
        }
      }
    ))

    identify = ws.recv()
    if not identify:
      raise InvalidToken("Invalid Discord account token used.")

    end = time.time()
    identify_json = json.loads(identify)
    self.logger = Logger(identify_json)
    self.user_id = int(identify_json["d"]["user"]["id"])
    self.session_id = identify_json["d"]["session_id"]
    self.logger.ws(f"Logged into bot in {round(end - start, 2)} seconds.")