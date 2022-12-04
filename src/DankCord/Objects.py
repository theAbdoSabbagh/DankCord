from typing import Optional

import orjson as json
import time
import faster_than_requests as requests


class Response:
    """
    Represents a Response class for an HTTP request.
    faster_than_requests returns: [body, type, status, version, url, length, headers]
    which is passed as param `response`
    """

    def __init__(self, response: list) -> None:
        try:
            self.data: dict = json.loads(response[0])
        except:
            self.data = response[0]
        self.format = response[1]
        self.code = int(response[2].split(" ")[0])
        self.headers = response[6]


class Message:
    def __init__(self, data: dict, client) -> None:
        self.data: dict = data
        self.content: str = data["content"]
        self.id: int = data["id"]
        try:
            embed_list = data["embeds"]
            embed_objects = []
            self.embeds: list = []
            for i in embed_list:
                embed_objects.append(Embed(i))
            self.embeds = embed_objects
        except Exception as e:
            self.embeds = []
            raise e
        self.channel: int = int(data["channel_id"])
        self.timestamp: int = data["timestamp"]
        try:
            self.components: list = []
            self.buttons: list = []
            self.dropdowns: list = []
            actionrows = data["components"]
            actionrow_objects = []
            for i in actionrows:
                actionrow_objects.append(ActionRow(i, self.id, client))
            self.components = actionrow_objects
            button_objects = []
            dropdown_objects = []
            for i in self.components:
              for i2 in i.components:
                if isinstance(i2, Button):
                  button_objects.append(i2)
                if isinstance(i2, Dropdown):
                  dropdown_objects.append(i2)
            self.buttons = button_objects
            self.dropdowns = dropdown_objects
        except Exception as e:
            self.components: list = []
            raise e

    def fetch_button(self, label: str):
        returned_button = None
        for i in self.buttons:
          if i.label == label:
            returned_button = i
            break
        return returned_button


class Author:
    def __init__(self, data: dict) -> None:
        self.name: str = data.get("name", "")
        self.icon_url = data.get("icon_url", "")


class ActionRow:
    def __init__(self, data: dict, message_id: str, client):
        self.components = [
            Button(i, message_id, client) if i["type"] == 2 else Dropdown(i) for i in data["components"]
        ]


class DropdownOption:
    def __init__(self, data: dict) -> None:
        self.label: str = data["label"]
        self.default: bool = data.get("default", False)
        self.value: str = data.get("value", "")


class Dropdown:
    def __init__(self, data: dict) -> None:
        self.type = 3
        self.options = [DropdownOption(child) for child in data["options"]]
    # TODO: Make a choose function


class Button:
    def __init__(self, data: dict, message_id: str, client) -> None:
        self.client = client
        self.message_id = message_id
        self.type = 2
        self.emoji: Optional[Emoji] = Emoji(
            data["emoji"]) if "emoji" in data.keys() else None
        self.label: str = data.get("label", "")
        self.disabled: bool = data.get("disabled", False)
        self.custom_id: str = data.get("custom_id", "")

    def click(self, retry_attempts: int=3):
        nonce = self.client._create_nonce()
        data = {
            "type": 3,
            "nonce": nonce,
            "guild_id": self.client.guild_id,
            "session_id": self.client.session_id,
            "channel_id": self.client.channel_id,
            "message_flags": 0,
            "message_id": self.message_id,
            "application_id": "270904126974590976",
            "data": {
                "component_type": 2,
                "custom_id": self.custom_id
            }
        }
        for i in range(retry_attempts):
            response = Response(
                requests.post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    json.dumps(data),
                    http_headers=self.client._tupalize(
                        {
                            "Authorization": self.client.token,
                            "Content-Type": "application/json",
                        }
                    ),
                )
            )
            if isinstance(response.data, dict):
              retry_after = int(response.data.get("retry_after", 0))
              time.sleep(retry_after)
            else:
              break


class Emoji:
    def __init__(self, data: dict) -> None:
        self.name: str = data["name"]
        self.id: int = data["id"]


class EmbedFooter:
    def __init__(self, data: dict) -> None:
        self.text: str = data.get("text", "")
        self.icon_url: str = data.get("icon_url", "")
        self.proxy_icon_url: str = data.get("proxy_icon_url", "")


class Embed:
    def __init__(self, data: dict) -> None:
        self.title: str = data.get("title", "")
        self.description: str = data.get("description", "")
        self.url: str = data.get("url", "")
        self.author: Author = Author(
            data["author"]) if "author" in data else None
        self.footer: Optional[EmbedFooter] = (
            EmbedFooter(data["footer"]) if "footer" in data else None
        )


class Bot:
    def __init__(self, data: dict) -> None:
        self.username: str = data["d"]["user"]["username"]
        self.id: int = int(data["d"]["user"]["id"])
        self.discriminator: int = int(data["d"]["user"]["discriminator"])
        self.email: str = data["d"]["user"]["email"]
        self.bot: str = f"{self.username}#{self.discriminator}"
