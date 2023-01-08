from typing import Optional, Literal, Callable, Union
from time import time, sleep
from json import load

from pyloggor import pyloggor

from .exceptions import InvalidFormBody
from .api import API
from .objects import Message, User, Config
from .gateway import Gateway

class Utilities(API):
    def __init__(
        self,
        config: Config,
        commands_data: dict,
        guild_id : Optional[int],
        session_id : Optional[str],
        logger: pyloggor,
        user: User,
        gateway: Gateway
    ) -> None:
        self.config: Config = Config
        self.token = config.token
        self.resource_intensivity = config.resource_intensivity
        self.channel_id = config.channel_id
        self.dm_mode = config.dm_mode
        self.commands_data = commands_data
        self.guild_id: Optional[int] = guild_id
        self.session_id: Optional[str] = session_id
        self.logger = logger
        self.user: User = user
        self.ws_cache = {}
        self.gateway: Gateway = gateway

    def _get_command_info(self, name: str) -> dict:
        """Retuns information about a given command.
        
        Parameters
        --------
        name: str
            The name of the command.
            
        Returns
        --------
        information: dict
        """
        if self.resource_intensivity == "MEM":
            return self.commands_data.get(name, {})
        else:
            return load(open(f"{self.channel_id}_commands.json", "r+")).get(name, {})

    def wait_for(
        self,
        event: Literal["MESSAGE_CREATE", "MESSAGE_UPDATE", "INTERACTION_CREATE", "INTERACTION_SUCCESS"],
        check: Optional[Callable[..., bool]] = None,
        timeout: float = 10
    ) -> Optional[Union[Message, bool]]:
        """
        Waits for a WebSocket event to be dispatched.

        This could be used to wait for a message to be sent or a message to be edited,
        or even to confirm an interaction being created or successful.

        The `timeout` parameter specifies how long to wait for until the desired event
        is dispatched; if the event was not dispatched before the timeout duration is over,
        it returns `None`.

        This function returns the **first event that meets the requirements**.

        Example
        ---------

        Waiting for a message to be sent:

            def DankMemerShop():
                def check(message: Message):
                    # The author ID is the ID of Dank Memer
                    return message.author.id == 270904126974590976 and "shop" in message.embeds[0].title.lower()
                
                message: Message = bot.wait_for("MESSAGE_CREATE", check = check)

        Parameters
        ------------
        event: str
            The event name.
        check: Optional[Callable[..., `bool`]]
            A predicate to check what to wait for. The arguments must meet the
            parameters of the event being waited for.
        timeout: Optional[`float`]
            The number of seconds to wait before timing out and returning `None`.

        Returns
        --------
        Optional[Union[Message, bool]]
            Returns the Message object, or a boolean.
        """
        limit = time() + timeout
        if check is None:
            def _check(*args):
                return True
            check = _check

        while time() < limit:
            try:
                cache = self.gateway.cache            
                if event == "INTERACTION_CREATE":
                    if check(cache.interaction_create[-1]):
                        return True
                if event =="INTERACTION_SUCCESS":
                    if check(cache.interaction_success[-1]):
                        return True

                if event == "MESSAGE_CREATE":
                    value = list(cache.message_create.values())[-1]
                    _msg = Message(value)
                    if check(_msg) is True:
                        return _msg
                if event == "MESSAGE_UPDATE":
                    while len(cache.raw_message_updates) == 0:
                        continue
                    _msg = Message(cache.raw_message_updates[-1])
                    if check(_msg) is True:
                        return _msg
            except:
                pass
        
        return None

    def scrape_inventory(
        self,
        user: Union[Optional[str], Optional[int]] = None,
        page: int = 1,
        single_page: bool = False,
        scroll_cooldown: float = 2
    ) -> Optional[dict[dict, str]]:
        """Scrapes a user's inventory.

        Parameters
        ----------
        user: Union[Optional[str], Optional[int]]
            The ID of the user to scrape. Defaults to the ID of the bot itself.
        page: int
            The page to start scraping at. Defaults to 0.
        single_page: bool
            Whether to scrape the single page specified or scrape all pages. Defaults to False.
        scroll_cooldown: float
            The cooldown to wait for before moving to the next page.

        Returns
        --------
        inventory: Optional[`dict`[`dict`, `str`]]
            The inventory of the user. Could be None.
        """
        message: Optional[Message] = self.run_command(
            "inventory",
            user = str(user) if user is not None else str(self.user.id),
            page = page
        )

        if not message:
            return None
        
        def check(m: Message):
            return m.id == message.id
        
        inventory = {"items": {}}

        pages_count = int(message.embeds[0].footer.text.split('of ')[1]) - 1 # Minus 1 cause the page starts always at 1
        for page in range(pages_count):
            for line in message.embeds[0].description.splitlines():
                if not '─' in line:
                    continue
                line = line.replace('*', '').replace('`', '')
                split_by = ">" if ">" in line else ":"
                try:
                    item_name = line.split(f'{split_by} ')[-1].split(' ─')[0]
                    item_quantity = line.split(f'{split_by} ')[1].split(' ─ ')[1]
                except IndexError:
                    pass
                else:
                    inventory["items"][item_name] = item_quantity
                
            if single_page:
                inventory["status"] = "Success"
                return inventory
            
            try:
                success_state = self.click(message.buttons[2])
            except InvalidFormBody as e:
                inventory["status"] = f"Failed due to error: {e}"
                return inventory
             
            if not success_state:
                inventory["status"] = "Failed to move to next page due to API limits"
                return inventory
            
            message: Optional[Message] = self.wait_for(
                "MESSAGE_UPDATE",
                check = check
            )

            sleep(scroll_cooldown)

        inventory["status"] = "Success"
        return inventory
