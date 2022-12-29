import datetime, json, time
import requests

from rich import print
from typing import Callable, Literal, Optional, Union
from pyloggor import pyloggor
from requests import Response

from .exceptions import DataAccessFailure, MissingPermissions, NoCommands, UnknownChannel
from .gateway import Gateway
from .Objects import Config, Message, User
from .core import Core
from .api import API

class Client(API):
    def __init__(self, config: Config, logger: pyloggor):
        __boot_start = time.perf_counter()
        logger.log(level="Info", msg="Booting up DankCord client.")
        self.token = config.token
        self.logger = logger

        self.channel_id: str = str(config.channel_id)
        self.dm_mode = config.dm_mode

        self.resource_intensivity = config.resource_intensivity
        self.commands_data = {}
        self.ws_cache = {}

        self.gateway = Gateway(config, self.logger)
        if not self.gateway:
            raise ConnectionError("Failed to connect to gateway.")

        self.ws = self.gateway.ws
        self.session_id: Optional[str] = self.gateway.session_id

        if not config.dm_mode:
            self.guild_id = self.gateway.guild_id

        self._get_commands()
        self._get_info()

        logger.log(
            level="Info", msg=f"Fully booted up, it took total {round(time.perf_counter() - __boot_start, 3)} seconds."
        )
        self.core = Core(config, self.commands_data, self.guild_id, self.session_id, self.logger, self.gateway)

    def _get_commands(self, channel_id: Optional[str] = None) -> Optional[Response]:
        """Gets all slash command data in a channel, dumps them into memory or a file based on user settings.
        
        Parameters
        ---------
        channel_id: Optional[`str`]
            The channel ID, used for finding a channel and getting slash commands from.

        Raises
        ---------
        UnknownChannel
            Bot doesn't have access to this channel.
        MissingPermissions
            Bot cannot view the channel or read it's content.
        NoCommands
            No commands found.

        Returns
        ---------
        response: Optional[`Response`]
        """
        channel_id = channel_id or self.channel_id
        response = requests.get(  # type: ignore
                f"https://discord.com/api/v9/channels/{channel_id}/application-commands/search?type=1&application_id=270904126974590976",
                headers={"Authorization": self.token, "Content-type": "application/json"},
        )

        if isinstance(response, str):
            return response

        data = response.json()

        if data.get("code") == 10003:
            raise UnknownChannel("Bot doesn't have access to this channel.")
        if data.get("code") == 50013:
            raise MissingPermissions("Bot cannot view the channel or read it's content.")

        if "application_commands" not in data:
            raise NoCommands("No commands found.")

        if self.resource_intensivity == "MEM":
            self.commands_data = {
                command_data["name"]: command_data for command_data in data["application_commands"]
            }
        else:
            with open(f"{self.channel_id}_commands.json", "w") as f:
                json.dump(
                    {command_data["name"]: command_data for command_data in data["application_commands"]},
                    f,
                    indent=4,
                    sort_keys=True,
                )

        return response

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
            return json.load(open(f"{self.channel_id}_commands.json", "r+")).get(name, {})

    def _get_info(self) -> None:
        """Saves information about the bot user account.
        
        Raises
        -------
        DataAccessFailure
            Failed to get user info.
        """
        resp = requests.get(  # type: ignore
                "https://discord.com/api/v10/users/@me",
                headers={"Authorization": self.token, "Content-type": "application/json"},
            )
        if resp.status_code!= 200:
            raise DataAccessFailure("Failed to get user info.")
        self.user = User(resp.json())

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
        limit = time.time() + timeout
        if check is None:
            def _check(*args):
                return True
            check = _check

        while time.time() < limit:
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
        return None
