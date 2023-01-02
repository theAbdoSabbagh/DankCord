from typing import Literal, Optional, Union
from rich import print
from re import findall
from datetime import datetime

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
        self.value: Optional[str] = data.get("value", None)
        self.value: str = data.get("value", None)


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
        self.title: str = data.get("title", None)
        self.description: str = data.get("description", None)
        self.authorName : str = data.get("author", {}).get("name", None)
        self.url: str = data.get("url", None)
        self.author: Optional[Author] = Author(data["author"]) if "author" in data else None
        self.footer: Optional[EmbedFooter] = EmbedFooter(data["footer"]) if "footer" in data else None


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

class CommandResult:
    """
    Represents a class that has the result of running a certain command.
    """
    
    def __init__(self, success: bool, death: bool = False, gain: dict = {}, loss: dict = {}, cooldown: int = None) -> None:
        self.success: Optional[bool] = success
        self.death: Optional[bool] = death
        self.gain: Optional[dict] = gain
        self.loss: Optional[dict] = loss
        self.cooldown: Optional[int] = cooldown
        if self.cooldown:
            self.cooldown = round(self.cooldown, 2)

class Parser:
    """
    Extracts crucial data from the result of a command, such as coins, gain, loss anad deaths.
    """
    def beg(description: str):
        """
        Parses crucial information from the descriptions of the beg command.
        """
        gain_regex = ["\*\*⏣ [0-9]+\*\*", "[0-9]+", "\*\*(.*?)\*\*", "<(.*?)\>"]
        temp_desc = description.replace(",", "")
        death = None
        success = True
        gain = {}
        gained_coins = None
        gained_item = None
        try:
            gained_coins = int(findall(gain_regex[1], findall(gain_regex[0], temp_desc)[0])[0])
        except:
            pass
        try:
            if not gained_coins:
                gained_item = findall(gain_regex[2], temp_desc)[0]
                tempstring = "<" + findall(gain_regex[3], gained_item)[0] + "> "
                item = item.replace(tempstring, "")
            else:
                gained_item = findall(gain_regex[2], temp_desc)[1]
                tempstring = "<" + findall(gain_regex[3], gained_item)[0] + "> "
                gained_item = gained_item.replace(tempstring, "")
        except:
            pass
        if gained_coins:
            gain["coins"] = gained_coins
        if gained_item:
            gain["items"] = [{1: gained_item}]
        success = not gained_coins is None or not gained_item is None
        return CommandResult(success, death, gain)
    
    def search(description: str):
        """
        Parses crucial information from the descriptions of the search command.
        """
        gain_regex = ["\*\*⏣ [0-9]+\*\*", "[0-9]+"]
        gain = {}
        temp_desc = description.replace(",", "")
        item_amount = None
        item = None
        try:
            item_amount = int(findall("\*\*[0-9]+x", temp_desc)[0].replace("**", "").replace("x", ""))
            item = " ".join(findall("\*\*[0-9]+x .+\*\*", temp_desc)[0].replace("**", "").split(" ")[2:])
        except:
            pass
        death = None
        success = True
        gained_coins = None
        try:
            gained_coins = int(findall(gain_regex[1], findall(gain_regex[0], temp_desc)[0])[0])
        except:
            success = False
        if gained_coins:
             gain["coins"] = gained_coins
        if item_amount:
            gain["items"] = [{item_amount: item}]
        return CommandResult(success, death, gain)

    def common1(description: str):
        """
        Parses crucial information from the descriptions of the fish, hunt and dig commands.
        """
        temp_desc = description.replace(",", "")
        gain_regex = ["\*\*.*\*"]
        gained_items = None
        success = True
        death = None
        gain = {}
        try:
            gained_items =  " ".join(findall(gain_regex[0], temp_desc)[0].replace("**", "").split(" ")[1:])
        except:
            success = False
        if gained_items:
            gain["items"] = [{1: gained_items}]
        return CommandResult(success, death, gain)
        
    def crime(description: str):
        """
        Parses crucial information from the descriptions of the crime command.
        """
        gain_regex = ["\*\*⏣ [0-9]+\*\*", "[0-9]+", "<(.*?)\>", "\*\*(.*?)\*\*"]
        gain = {}
        temp_desc = description.replace(",", "")
        item = None
        death = None
        success = False
        gained_coins = None
        try:
            gained_coins = int(findall(gain_regex[1], findall(gain_regex[0], temp_desc)[0])[0])
        except:
            pass
        try:
            if not gained_coins:
                item = findall(gain_regex[3], temp_desc)[0]
                tempstring = "<" + findall(gain_regex[2], item)[0] + "> "
                item = item.replace(tempstring, "")
            else:
                item = findall(gain_regex[3], temp_desc)[1]
                tempstring = "<" + findall(gain_regex[2], item)[0] + "> "
                item = item.replace(tempstring, "")
        except:
            pass
        if gained_coins:
             gain["coins"] = gained_coins
        if item:
            gain["items"] = [{1: item}]
        success = not gained_coins is None or not item is None
        return CommandResult(success, death, gain)
    
    def postmemes(description: str):
        """
        Parses crucial information from the descriptions of the postmemes command.
        """
        parsed = description.replace(",", "").split("\n")[3:]
        try:
            index = parsed.index("**You Received:**")
            parsed = parsed[index:]
        except ValueError:
            pass
        gain = {}
        success = True
        death = None
        gain_regex = ["[0-9]+", "[0-9]+x"]
        if "**You Received" in description:
            for i in parsed:
                if "⏣" in i:
                    gain["coins"] = int(findall(gain_regex[0], i)[0])
                elif "<:" in i:
                    if not "items" in gain.keys():
                        gain["items"] = []
                    amount = int(findall(gain_regex[1], i)[0].replace('x', ''))
                    item = " ".join(i.split(" ")[5:])
                    gain["items"].append({amount: item})
        else:
            success = False
        return CommandResult(success, death, gain)
    
    def cooldown(description: str):
        """
        Parses crucial information from the descriptions of the cooldown indicator.
        """
        cooldown_regex = ["<(.*?)\>", "(\d+)"]
        time = datetime.fromtimestamp(int(findall(cooldown_regex[1], findall(cooldown_regex[0], description)[0])[0]))
        difference = (time - datetime.now()).total_seconds()
        return CommandResult(False, None, {}, cooldown=difference)
    
    def check_cooldown(description: str):
        """
        Checks if the returned embed is a cooldown message.
        """
        try:
            if "seconds" in description and "command" in description and "cooldown is" in description and "seconds" in description:
                return True
            else:
                return False
        except:
            return False
        
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