from typing import Literal, Optional

import orjson


class Config:
    def __init__(
        self,
        token: str,
        channel_id: Optional[int],
        dm_mode: bool = False,
        resource_intensivity: Literal["DISK", "MEM"] = "MEM",
    ) -> None:
        if not token:
            raise ValueError("No token provided.")
        if not channel_id:
            raise ValueError("No channel_id provided.")

        assert isinstance(token, str)
        assert isinstance(channel_id, int)
        assert resource_intensivity.upper() in ("DISK", "MEM")

        self.token = token
        self.channel_id = channel_id
        self.dm_mode = dm_mode
        self.resource_intensivity = resource_intensivity.upper()


class Cache:
    def __init__(self) -> None:
        """
        Holds relevant websocket message events.
        """
        self.nonce_message_map = {}
        self.interaction_create = []
        self.interaction_success = []
        self.message_create = {}
        self.message_updates = {}

    def clear(self, nonce):
        if nonce in self.nonce_message_map:
            relevant_id = self.nonce_message_map[nonce]
            del self.nonce_message_map[nonce]
            if relevant_id in self.message_updates:
                del self.message_updates[relevant_id]
        if nonce in self.interaction_create:
            self.interaction_create.remove(nonce)
        if nonce in self.interaction_success:
            self.interaction_success.remove(nonce)
        if nonce in self.message_create:
            del self.message_create[nonce]


class Response:
    """
    Represents a Response class for an HTTP request.
    faster_than_requests returns: [body, type, status, version, url, length, headers]
    which is passed as param `response`
    """

    def __init__(self, response: list) -> None:
        try:
            self.data: dict = orjson.loads(response[0])
        except:
            self.data = response[0]
        self.format = response[1]
        self.code: int = int(response[2].split(" ")[0])
        self.headers: str = response[6]


class Author:
    """
    A class that represents the author of some context.
    """

    def __init__(self, data: dict) -> None:
        self.name: str = data.get("name", None)
        self.icon_url = data.get("icon_url", None)


class ActionRow:
    """
    Represents an ActionRow.
    """

    def __init__(self, data: dict, message_id: str):
        self.components = [
            Button(i, message_id) if i["type"] == 2 else Dropdown(i, message_id) for i in data["components"]
        ]


class DropdownOption:
    """
    Represents a Dropdown Option.
    """

    def __init__(self, data: dict) -> None:
        self.label: str = data["label"]
        self.default: bool = data.get("default", False)
        self.value: str = data.get("value", None)


class Dropdown:
    """
    Represents a Dropdown component.
    """

    def __init__(self, data: dict, message_id: str) -> None:
        self.message_id = message_id
        self.type = 3
        self.custom_id: Optional[int] = data.get("custom_id", None)
        self.options = [DropdownOption(child) for child in data["options"]]

    # TODO: Make a choose function


class Button:
    """
    Represents a button from the Discord Bot UI Kit.
    """

    def __init__(self, data: dict, message_id: str) -> None:
        self.message_id: str = message_id
        self.type: int = 2
        self.emoji: Optional[Emoji] = Emoji(data["emoji"]) if "emoji" in data.keys() else None
        self.label: Optional[str] = data.get("label", None)
        self.disabled: Optional[bool] = data.get("disabled", False)
        self.custom_id: Optional[str] = data.get("custom_id", None)


class Emoji:
    """
    Represents a custom emoji.
    """

    def __init__(self, data: dict) -> None:
        self.name: Optional[str] = data.get("name", None)
        self.id: Optional[int] = data.get("id", None)


class EmbedFooter:
    """
    Represents an embed footer.
    """

    def __init__(self, data: dict) -> None:
        self.text: Optional[str] = data.get("text", None)
        self.icon_url: Optional[str] = data.get("icon_url", None)
        self.proxy_icon_url: Optional[str] = data.get("proxy_icon_url", None)


class Embed:
    """
    Represents a Discord embed.
    """

    def __init__(self, data: dict) -> None:
        self.title: str = data.get("title", None)
        self.description: str = data.get("description", None)
        self.url: str = data.get("url", None)
        self.author: Author = Author(data["author"]) if "author" in data else None
        self.footer: Optional[EmbedFooter] = EmbedFooter(data["footer"]) if "footer" in data else None
        self.data: dict = data


class Message:
    """
    Represents a message from Discord.
    """

    def __init__(self, data: dict) -> None:
        self.content: str = data["content"]
        self.data: dict = data
        self.id: int = data["id"]
        self.timestamp: int = data["timestamp"]
        self.channel: int = int(data["channel_id"])
        self.embeds: list = [Embed(i) for i in data.get("embeds", [])]
        self.components: list = [ActionRow(i, self.id) for i in data.get("components", [])]
        self.buttons: list = [
            item for component in self.components for item in component.components if isinstance(item, Button)
        ]
        self.dropdowns: list = [
            item for component in self.components for item in component.components if isinstance(item, Dropdown)
        ]


class Bot:
    """
    Represents the bot account.
    """

    def __init__(self, data: dict) -> None:
        self.username: str = data["d"]["user"]["username"]
        self.id: int = int(data["d"]["user"]["id"])
        self.discriminator: int = int(data["d"]["user"]["discriminator"])
        self.email: str = data["d"]["user"]["email"]
        self.bot: str = f"{self.username}#{self.discriminator}"
