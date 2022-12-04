from typing import Optional

import orjson as json


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
    def __init__(self, data: dict) -> None:
        self.data: dict = data
        self.content: str = data["content"]

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

        self.author: Author = Author(data["author"])
        self.channel: int = int(data["channel_id"])
        self.timestamp: int = data["timestamp"]

        try:
            self.components: list = []
            actionrows = data["components"]
            actionrow_objects = []
            for i in actionrows:
                actionrow_objects.append(ActionRow(i))
            self.components = actionrow_objects
        except Exception as e:
            self.components: list = []
            raise e


class Author:
    def __init__(self, data: dict) -> None:
        self.username: str = data["username"]
        self.id: int = int(data["id"])
        self.discriminator: int = int(data["discriminator"])
        self.bot: bool = data["bot"]


class ActionRow:
    def __init__(self, data: dict):
        self.components = [
            Button(i) if i["type"] == 2 else Dropdown(i) for i in data["components"]
        ]


class DropdownOption:
    def __init__(self, data: dict) -> None:
        self.label: str = data["label"]
        self.default: bool = data.get("default", False)


class Dropdown:
    def __init__(self, data: dict) -> None:
        self.type = 3
        self.options = [DropdownOption(child) for child in data["options"]]

    # TODO: Make a choose function


class Button:
    def __init__(self, data: dict) -> None:
        self.type = 2
        self.emoji: Optional[Emoji] = Emoji(data["emoji"]) if data["emoji"] else None
        self.label: str = data.get("label", "")

        self.disabled: bool = data.get("disabled", False)
        self.custom_id: str = data.get("custom_id", "")

    # TODO: Make a click function


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
        self.descriptio: str = data.get("description", "")
        self.url: str = data.get("url", "")
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
