import faster_than_requests as requests
import json, datetime, time

from rich import print, print_json
from typing import Optional, Union
from .Objects import Response, Message
from .exceptions import InvalidToken, UnknownChannel
from .ws import Gateway
from string import printable
from threading import Thread

class Client:
  def __init__(self, token: str, channel_id: id):
    self.token = token
    self.channel_id = channel_id
    self.guild_id = self._get_guild_id()

    self.gateway = Gateway(self.token)
    self.ws = self.gateway.ws
    self.ws_cache = {}

    self.session_id: Optional[str] = self.gateway.session_id
    self.user_id: Optional[int] = self.gateway.user_id
    self.dankmemer = DankMemer(self.token)
    self._get_commands()
    t1 = Thread(target = self._events_listener)
    t1.daemon = True
    t1.start()

  def _strip(self, content: str) -> str:
    return "".join([char for char in content if char in printable])

  def _tupalize(self, dict):
    return [(a, b) for a, b in dict.items()]

  def _get_guild_id(self):
    response = Response(requests.get(url=f"https://discord.com/api/v10/channels/{self.channel_id}", http_headers=[("Authorization", self.token)]))
    guild_id = response.data.get('guild_id')
    if guild_id is None:
      raise InvalidToken("Invalid Discord account token used.")
    return guild_id

  def _create_nonce(self):
    return str(int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000 - 1420070400000) << 22)

  def _get_commands(self, channel_id: int = None):
    channel_id = channel_id or self.channel_id
    response = self.dankmemer.get_commands(channel_id)
    if isinstance(response, str):
      return response
    if response.data.get('code') == 10003:
      raise UnknownChannel("Bot doesn't have access to this channel.")
    data = {}
    for command_data in response.data.get('application_commands'):
      data[command_data["name"]] = command_data
    with open("commands.json", "w+") as f:
      f.write(json.dumps(data, indent=2, sort_keys=False))
    return response

  def _get_command_info(self, name: str):
    with open("commands.json", "r+") as f:
      data = json.loads(f.read())
    return data[name]

  def _confirm_command_ran(self, nonce_used: str, timeout: int):
    end = time.time() + timeout
    while time.time() < end:
      recieved_nonce = json.loads(self.ws.recv())
      try:
        if str(recieved_nonce["d"]["nonce"]) == str(nonce_used):
          return recieved_nonce["d"]
      except:
        pass
    return None

  def _events_listener(self):
    while True:
      event = json.loads(self.ws.recv())
      try:
        if event["d"]["channel_id"] == str(self.channel_id) or event["d"]["channel_id"] == "270904126974590976":
          self.ws_cache[event["d"]["nonce"]] = event["d"]
      except:
        pass

  def _OptionsBuilder(self, name, type_, **kwargs):
    options = [
      {
        "type": type_,
        "name": name,
        "options": [
        ]
      }
    ]

    type_types = {
      str: 3,
      bool: 5,
      list: 2,
      int: 10
    }

    option_type = 3
    for key, value in kwargs.items():
      option_type = type_types[type(value)]
      new_piece_of_data = {
        "type": option_type,
        "name": key,
        "value": value
      }
      options[0]["options"].append(new_piece_of_data)

    return options

  def get_info(self) -> Response:
    return Response(requests.get(url="https://discord.com/api/v10/users/@me", http_headers=[("Authorization", self.token)]))

  def run_command(self, /, name: str, retry=False, attempts=10, timeout: int = 10):
    nonce = self._create_nonce()
    command_info = self._get_command_info(name)
    attempts = attempts if attempts > 0 else 1
    data = {
        "type": 2,
        "application_id": "270904126974590976",
        "guild_id": self.guild_id,
        "channel_id": self.channel_id,
        "session_id": self.session_id,
        "data": {
            "version": command_info["version"],
            "id": command_info["id"],
            "name": name,
            "type": 1,
            "options": [],
            "application_command": {
                "id": command_info["id"],
                "application_id": "270904126974590976",
                "version": command_info["version"],
                "default_permission": command_info["default_permission"],
                "default_member_permissions": command_info["default_member_permissions"],
                "type": 1,
                "name": name,
                "description": command_info["description"],
                "dm_permission": command_info["dm_permission"],
            },
            "attachments": []
        },
        "nonce": nonce
    }
    for i in range(attempts):
      response = requests.post("https://discord.com/api/v9/interactions", json.dumps(data), http_headers=[("Authorization", self.token), ("Content-Type", "application/json")])
      message_data = self._confirm_command_ran(nonce, timeout)
      status = not message_data is None
      if retry is False or status is True:
        break
    if status:
      while not str(nonce) in self.ws_cache.keys():
        time.sleep(0.00001)
      message_data = self.ws_cache[str(nonce)]
      message_object = Message(message_data)
      return message_object
    else:
      return None

  def run_sub_command(self, /, name: str, sub_name: str, retry=False, attempts=10, timeout: int = 10, **kwargs):
    nonce = self._create_nonce()
    command_info = self._get_command_info(name)
    attempts = attempts if attempts > 0 else 1
    type_ = 1
    for item in command_info["options"]:
      if item["name"] == sub_name:
        type_ = item["type"]
        break
    data = {
      "type": 2,
      "application_id": "270904126974590976",
      "guild_id": self.guild_id,
      "channel_id": self.channel_id,
      "session_id": self.session_id,
      "data": {
          "version": command_info["version"],
          "id": command_info["id"],
          "name": name,
          "type": command_info["type"],
          "options": self._OptionsBuilder(sub_name, type_, **kwargs),
          "application_command": {
              "id": command_info["id"],
              "application_id": "270904126974590976",
              "version": command_info["version"],
              "default_permission": command_info["default_permission"],
              "default_member_permissions": command_info["default_member_permissions"],
              "type": command_info["type"],
              "name": name,
              "description": command_info["description"],
              "dm_permission": command_info["dm_permission"],
              "options": command_info["options"]
          },
          "attachments": []
        },
        "nonce": nonce
    }
    for i in range(attempts):
      requests.post("https://discord.com/api/v9/interactions", json.dumps(data), http_headers=[("Authorization", self.token), ("Content-Type", "application/json")])
      message_data = self._confirm_command_ran(nonce, timeout)
      status = not message_data is None
      if retry is False or status is True:
        break
    if status:
      while not str(nonce) in self.ws_cache.keys():
        time.sleep(0.00001)
      message_data = self.ws_cache[str(nonce)]
      message_object = Message(message_data)
      return message_object
    else:
      return None

# Whatever is below is being worked on

class PepeCaptcha:
  def __init__(self) -> None:
    pass


class EmojiCaptcha:
  def __init__(self) -> None:
    pass


class DankMemer:
  def __init__(self, token: str) -> None:
    self.token = token
    self.emoji_ids = [
      819014822867894304, 796765883120353280,
      860602697942040596,  860602923665588284,
      860603013063507998, 936007340736536626,
      933194488241864704, 680105017532743700
    ]

  @property
  def captcha_types(self) -> Union[PepeCaptcha, EmojiCaptcha]:
    return PepeCaptcha, EmojiCaptcha

  @property
  def captcha_emojis(self) -> list:
    return self.emoji_ids

  def get_commands(self, channel_id: int) -> Response:
    response = Response(requests.get(f"https://discord.com/api/v9/channels/{channel_id}/application-commands/search?type=1&application_id=270904126974590976", http_headers=[("Authorization", self.token)]))
    return response
