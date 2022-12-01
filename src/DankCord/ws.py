import threading, random, time, json

from rich import print
from websocket import create_connection

from .exceptions import InvalidToken

class Gateway:
  def __init__(self, token : str):
    print(f"Booting up a local discord signal client.")
    self.session_id = None
    self.token = token

    self.__boot_ws()

  def heartbeat(self):
    while True:
      time.sleep(self.heartbeat_interval)
      self.ws.send(json.dumps({"op": 1, "d": None}))

  def __boot_ws(self):
    print("Booting up the discord websocket client.")
    ws = create_connection("wss://gateway.discord.gg/?v=9&encoding=json")

    hello = json.loads(ws.recv())

    self.ws = ws
    self.heartbeat_interval = hello["d"]["heartbeat_interval"]/1000
    print("Booting up the discord heartbeat client.")

    jitter_heartbeat = self.heartbeat_interval * random.uniform(0, 0.1)

    time.sleep(jitter_heartbeat)
    ws.send(json.dumps({"op": 1, "d": None}))
    response = json.loads(ws.recv())

    if response["op"] != 11:
      print("Discord heartbeat client failed to boot.")
      return False

    thread = threading.Thread(target = self.heartbeat).start()
    print("Booted up the discord heartbeat client. Now IDENTIFYING")

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

    identify_json = json.loads(identify)
    self.session_id = identify_json["d"]["session_id"]
    print("READY")
