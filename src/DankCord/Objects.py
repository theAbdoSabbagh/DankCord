from typing import Literal, Optional, Union
from rich import print

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

        assert isinstance(token, str), "Bot token must be of type str."
        assert isinstance(channel_id, int), "Channel ID must be of type int."
        assert resource_intensivity.upper() in ("DISK", "MEM"), "Resource intensivity option must be either DISK or MEM."

        self.token: str = token
        self.channel_id: int = channel_id
        self.dm_mode: bool = dm_mode
        self.resource_intensivity: str = resource_intensivity.upper()


class Cache:
    def __init__(self) -> None:
        """
        Holds relevant websocket message events.
        """
        self.nonce_message_map = {}
        self.interaction_create = []
        self.interaction_success = []
        self.raw_message_updates = []
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
        self.raw_message_updates = []


class Author:
    """
    A class that represents the author of some context.
    """

    def __init__(self, data: dict) -> None:
        self.name: Optional[str] = data.get("name", None)
        self.discriminator: Optional[str] = data.get("discriminator", None)
        self.icon_url: Optional[str] = data.get("icon_url", None)
        self.id: Optional[int] = int(data.get("id", 0))
    
    def __repr__(self) -> str:
        return f"{self.name}#{self.discriminator}"


class ActionRow:
    """
    Represents an ActionRow.
    """

    def __init__(self, data: dict, message_id: Union[str, int]):
        message_id = str(message_id) # type: ignore
        self.components: list[Button | Dropdown] = [
            Button(i, message_id) if i["type"] == 2 else Dropdown(i, message_id) for i in data["components"]
        ]
    

class DropdownOption:
    """
    Represents a Dropdown Option.
    """

    def __init__(self, data: dict) -> None:
        self.label: Optional[str] = data.get("label", None)
        self.default: bool = data.get("default", False)
        self.value: Optional[str] = data.get("value", None)


class Dropdown:
    """
    Represents a Dropdown component.
    """

    def __init__(self, data: dict, message_id: str) -> None:
        self.message_id: str = message_id
        self.type: int = 3
        self.custom_id: Optional[int] = data.get("custom_id", None)
        self.options: list[DropdownOption] = [DropdownOption(child) for child in data["options"]]

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
        self.data: dict = data
        self.title: Optional[str] = data.get("title", None)
        self.description: Optional[str] = data.get("description", None)
        self.url: Optional[str] = data.get("url", None)
        self.author: Optional[Author] = Author(data.get("author", {})) if "author" in data else None
        self.footer: Optional[EmbedFooter] = EmbedFooter(data.get("footer", {})) if "footer" in data else None


class Message:
    """
    Represents a message from Discord.
    """

    def __init__(self, data: dict) -> None:
        self.data: dict = data
        self.author: Optional[Author] = Author(data["author"]) if "author" in data else None
        self.content: Optional[str] = data.get("content", None)
        self.nonce: Optional[str] = data.get("nonce", None)
        self.id: Optional[int] = int(data.get("id", 0))
        self.timestamp: Optional[str] = data.get("timestamp", None)
        self.channel_id: Optional[int] = int(data.get("channel_id", 0))
        self.embeds: list[Embed] = [Embed(i) for i in data.get("embeds", [])]
        self.components: list[ActionRow] = [ActionRow(i, self.id) for i in data.get("components", [])]
        self.buttons: list[Button] = [
            item for component in self.components for item in component.components if isinstance(item, Button)
        ]
        self.dropdowns: list[Dropdown] = [
            item for component in self.components for item in component.components if isinstance(item, Dropdown)
        ]

class CommandResult:
    """
    Represents a class that has the result of running a certain command.
    """
    
    def __init__(
        self,
        success: bool = None,
        death: bool = None,
        coin_gain: int = None,
        coin_loss: int = None,
        items_gain: dict = None,
        items_loss: dict = None,
    ) -> None:
        self.success: Optional[bool] = success
        self.death: Optional[bool] = death
        self.coin_gain: Optional[int] = coin_gain
        self.coin_loss: Optional[int] = coin_loss
        self.items_gain: Optional[dict] = items_gain
        self.items_loss: Optional[dict] = items_loss


class User:
    """
    Represents a class that has the data of a user.
    """

    def __init__(self, data: dict) -> None:
        self.id: Optional[int] = int(data.get("id", 0))
        self.discriminator: Optional[int] = int(data.get("discriminator", 0))
        self.name: Optional[str] = data.get("username", None)
        self.bio: Optional[str] = data.get("bio", None)
        self.phone: Optional[str] = data.get("phone", None)
        self.email: Optional[str] = data.get("email", None)
        self.verified: bool = data.get("verified", False)