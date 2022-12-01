import json

class Response:
  def __init__(self, response: list) -> None:
    try:
      self.data = json.loads(response[0])
    except:
      self.data = response[0]
    self.format = response[1]
    self.code = int(response[2].split(" ")[0])
    self.headers = response[6]