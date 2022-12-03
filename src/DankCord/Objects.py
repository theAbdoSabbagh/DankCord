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
    self.data : dict = data
    self.content : str = data["content"]
    try:
      embed_list = data["embeds"]
      embed_objects = []
      self.embeds : list = []
      for i in embed_list:
        embed_objects.append(Embed(i))
      self.embeds = embed_objects
    except Exception as e:
      self.embeds = []
      raise e
    self.author : Author = Author(data["author"])
    self.channel : int = int(data["channel_id"])
    self.timestamp : int = data["timestamp"]
    try:
      self.components : list = []
      actionrows = data["components"]
      actionrow_objects = []
      for i in actionrows:
        actionrow_objects.append(ActionRow(i))
      self.components = actionrow_objects
    except Exception as e:
      self.components : list = []
      raise e

class Author:
  def __init__(self, data : dict) -> None:
    self.username : str = data["username"]
    self.id : int = int(data["id"])
    self.discriminator : int = int(data["discriminator"])
    self.bot : bool = data["bot"]

class ActionRow:
  def __init__(self, data: dict):
    components = data["components"]
    component_objects = []
    for i in components:
      if i["type"] == 2:
        component_objects.append(Button(i))
      if i["type"] == 3:
        component_objects.append(Dropdown(i))
    self.components = component_objects
    
class DropdownOption:
  def __init__(self, data : dict) -> None:
    self.label : str = data["label"]
    try:
      self.default : bool = data["default"]
    except:
      self.default : bool = False

class Dropdown:
  def __init__(self, data : dict) -> None:
    self.type = 3
    self.options = [DropdownOption(child) for child in data["options"]]
  # TODO: Make a choose function

class Button:
  def __init__(self, data : dict) -> None:
    self.type = 2
    try:
      self.emoji : Emoji = Emoji(data["emoji"])
    except:
      self.emoi = None
    try:
      self.label : str = data["label"]
    except:
      self.label : str = ""
    try:
      self.disabled : bool = data["disabled"]
    except:
      self.disabled : bool = False
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
    try:
      self.title : str = data["title"]
    except:
      self.title : str = ""
    try:
      self.description : str = data["description"]
    except:
      self.description : str = ""
    try:
      self.url : str = data["url"]
    except:
      self.url : str = ""
    try:
      self.footer : EmbedFooter = EmbedFooter(data["footer"])
    except:
      self.footer : EmbedFooter = None
      
class Bot:
  def __init__(self, data : dict) -> None:
    self.username : str = data["d"]["user"]["username"]
    self.id : int = int(data["d"]["user"]["id"])
    self.discriminator : int = int(data["d"]["user"]["discriminator"])
    self.email : str = data["d"]["user"]["email"]
    self.bot : str = f"{self.username}#{self.discriminator}"