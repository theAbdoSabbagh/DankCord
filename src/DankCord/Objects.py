import json as __json
import orjson as json

from rich import print_json

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
    self.content : str = data["d"]["content"]
    self.embeds : list = data["d"]["embeds"]
    self.author : Author = Author(data["author"])
    self.channel : int = int(data["d"]["channel_id"])
    self.timestamp : int = data["timestamp"]
    try:
      self.components : list = data["components"]
      # TODO: Convert each item in list to either DropDown or Button based on the type.
    except:
      self.components : list = []

class Author:
  def __init__(self, data : dict) -> None:
    self.username : str = data["username"]
    self.id : int = int(data["id"])
    self.discriminator : int = int(data["discriminator"])
    self.bot : bool = data["bot"]

class DropdownOption:
  def __init__(self, data : dict) -> None:
    self.label : str = data["label"]
    self.default : bool = data["default"]

class DropdownComponent:
  def __init__(self, data : dict) -> None:
    self.children = [DropdownOption(child) for child in data["options"]]
  
  # TODO: Make a choose function

class Button:
  def __init__(self, data : dict) -> None:
    self.emoji : Emoji = Emoji(data["emoji"])
    self.disabled : bool = data["disabled"]
    self.custom_id : str = data["custom_id"]

  # TODO: Make a click function

class Emoji:
  def __init__(self, data : dict) -> None:
    self.name : str = data["name"]
    self.id : int = data["id"]

class EmbedFooter:
  def __init__(self, data : dict) -> None:
    self.text : str = data["text"]
    self.icon_url : str = data["icon_url"]
    self.proxy_icon_url : str = data["proxy_icon_url"]

class Embed:
  def __init__(self, data : dict) -> None:
    # There's 2 types: rich and image, rich is the actual embed, image is image
    self.title : str = data["title"]
    self.description : str = data["description"]
    self.url : str = data["url"]
    self.footer : EmbedFooter = EmbedFooter(data["footer"])

class Bot:
  def __init__(self, data : dict) -> None:
    self.username : str = data["d"]["user"]["username"]
    self.id : int = int(data["d"]["user"]["id"])
    self.discriminator : int = int(data["d"]["user"]["discriminator"])
    self.email : str = data["d"]["user"]["email"]
    self.bot : str = f"{self.username}#{self.discriminator}"