import orjson as json

class Response:
  def __init__(self, response: list) -> None:
    try:
      self.data = json.loads(response[0])
    except:
      self.data = response[0]
    self.format = response[1]
    self.code = int(response[2].split(" ")[0])
    self.headers = response[6]
  
class Message:
  def __init__(self, data: dict) -> None:
    self.content = data["content"]
    self.embeds = data["embeds"]
    self.author = data["author"]
    self.channel = data["channel_id"]
    self.timestamp = data["timestamp"]
    try:
      self.components = data["components"]
    except:
      self.components = []