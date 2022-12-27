import datetime, json, time
import requests

from rich import print
from typing import Callable, Literal, Optional, Union
from pyloggor import pyloggor
from requests import Response

from .exceptions import DataAccessFailure, InvalidComponent, MissingPermissions, NoCommands, NonceTimeout, UnknownChannel
from .gateway import Gateway
from .Objects import Button, Config, Dropdown, Message, User
from .core import Core

class Client:
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

    def _create_nonce(self) -> str:
        """Creates a nonce using Discord's algorithm.
        
        Returns
        --------
        nonce: str"""
        return str(int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000 - 1420070400000) << 22)

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

    def _OptionsBuilder(self, name, type_, **kwargs):
        """Builds the data used in slash command API requests.
        
        Parameters
        --------
        name: Any
        type_: Any
        kwargs: **kwargs

        Returns
        --------
        options: list[`dict`[`str`, `Any`]]
        """
        options = [{"type": type_, "name": name, "options": []}]

        type_types = {str: 3, bool: 5, list: 2, int: 10}

        option_type = 3
        for key, value in kwargs.items():
            option_type = type_types[type(value)]
            new_piece_of_data = {"type": option_type, "name": key, "value": value}
            options[0]["options"].append(new_piece_of_data)

        return options

    def _RawOptionsBuilder(self, **kwargs):
        """Builds the raw data used in slash command API requests.
        
        Parameters
        --------
        kwargs: **kwargs

        Returns
        --------
        options: list
        """
        options = []

        type_types = {str: 3, bool: 5, list: 2, int: 10}

        option_type = 3
        for key, value in kwargs.items():
            option_type = type_types[type(value)]
            new_piece_of_data = {"type": option_type, "name": key, "value": value}
            options.append(new_piece_of_data)

        return options

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

    def run_command(self, name: str, retry_attempts: int = 3, timeout: int = 10, **kwargs) -> Optional[Message]:
        """Runs a slash command.

        Parameters
        --------
        name: str
            The command name.
        retry_attempts: int = 3
            The amount of times to retry on failure.
        timeout: int = 10
            Duration before it times out.
        kwargs: **kwargs

        Returns
        --------
        message: Optional[`Message`]
        """
        nonce = self._create_nonce()
        command_info = self._get_command_info(name)

        retry_attempts = retry_attempts if retry_attempts > 0 else 1
        type_ = 1
        options = []

        if command_info.get("options"):
            for item in command_info["options"]:
                if item["name"] == name:
                    type_ = item["type"]
                    break
            options = self._OptionsBuilder(name, type_, **kwargs)

        data = {
            "type": 2,
            "application_id": "270904126974590976",
            "guild_id": str(self.guild_id),
            "channel_id": self.channel_id,
            "session_id": self.session_id,
            "data": {
                "version": command_info["version"],
                "id": command_info["id"],
                "name": name,
                "type": 1,
                "options": options,
                "application_command": {
                    "id": command_info["id"],
                    "application_id": "270904126974590976",
                    "version": command_info["version"],
                    "default_permission": command_info["default_permission"],
                    "default_member_permissions": command_info["default_member_permissions"],
                    "type": 1,
                    "name": name,
                    "nsfw": command_info["nsfw"],
                    "description": command_info["description"],
                    "dm_permission": command_info["dm_permission"],
                },
                "attachments": [],
            },
            "nonce": nonce,
        }
        def check(message: Message):
            return message.nonce == nonce

        for i in range(retry_attempts):
            response = requests.post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    json=data,
                    headers={"Authorization": self.token, "Content-type": "application/json"}
                )
            
            try:
                interaction: Optional[Union[Message, bool]] = self.wait_for("MESSAGE_CREATE", check=check, timeout=timeout)
                return interaction # type: ignore
            except Exception as e:
                print(f"Error in run_command: {e}")
                continue
            
        return None

    def run_sub_command(self, name: str, sub_name: str, retry_attempts:int = 3, timeout: int = 10, **kwargs) -> Optional[Message]:
        """Runs a slash command.

        Parameters
        --------
        name: str
            The command name.
        sub_name: str
            The sub command name.
        retry_attempts: int = 3
            The amount of times to retry on failure.
        timeout: int = 10
            Duration before it times out.

        Returns
        --------
        message: Optional[`Message`]
        """

        nonce = self._create_nonce()
        command_info = self._get_command_info(name)
        retry_attempts = retry_attempts if retry_attempts > 0 else 1
        type_ = 1
        options = []

        if command_info.get("options"):
            for item in command_info["options"]:
                if item["name"] == name:
                    type_ = item["type"]
                    break
            options = self._OptionsBuilder(name, type_, **kwargs)

        data = {
            "type": 2,
            "application_id": "270904126974590976",
            "guild_id": str(self.guild_id),
            "channel_id": self.channel_id,
            "session_id": self.session_id,
            "data": {
                "version": command_info["version"],
                "id": command_info["id"],
                "name": name,
                "type": command_info["type"],
                "options": options,
                "application_command": {
                    "id": command_info["id"],
                    "application_id": "270904126974590976",
                    "version": command_info["version"],
                    "default_permission": command_info["default_permission"],
                    "default_member_permissions": command_info["default_member_permissions"],
                    "type": command_info["type"],
                    "name": name,
                    "nsfw": command_info["nsfw"],
                    "description": command_info["description"],
                    "dm_permission": command_info["dm_permission"],
                    "options": command_info["options"],
                },
                "attachments": [],
            },
            "nonce": nonce,
        }
        def check(message: Message):
            return message.nonce == nonce

        for i in range(retry_attempts):
            response = requests.post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    json=data,
                    headers={"Authorization": self.token, "Content-type": "application/json"}
                )
            
            try:
                message: Optional[Union[Message, bool]] = self.wait_for("MESSAGE_CREATE", check=check, timeout=timeout)
                return message # type: ignore
            except Exception as e:
                print(f"Error in run_sub_command: {e}")
                continue
        
        return None

    def run_slash_group_command(self, name: str, sub_name: str, sub_group_name: str, retry_attempts: int = 3, timeout: int = 10, **kwargs) -> Optional[Message]:
        """Runs a slash group command.

        Parameters
        --------
        name: str
            The command name.
        sub_name: str
            The sub command name.
        sub_group_name: str
            The sub group command name.
        retry_attempts: int = 3
            The amount of times to retry on failure.
        timeout: int = 10
            Duration before it times out.

        Returns
        --------
        message: Optional[`Message`]
        """

        nonce = self._create_nonce()
        command_info = self._get_command_info(name)
        retry_attempts = retry_attempts if retry_attempts > 0 else 1
        sub_type = 1
        sub_group_type = 1
        options = []

        if command_info.get("options"):
            for item in command_info["options"]:
                if item["name"] == sub_name:
                    sub_type = item["type"]
                for item_ in item["options"]:
                    if item_["name"] == sub_group_name:
                        sub_group_type = item_["type"]
            options = self._RawOptionsBuilder(**kwargs)

        data = {
            "type": 2,
            "application_id": "270904126974590976",
            "guild_id": str(self.guild_id),
            "channel_id": self.channel_id,
            "session_id": self.session_id,
            "data": {
                "version": command_info["version"],
                "id": command_info["id"],
                "name": name,
                "type": command_info["type"],
                "options": [
                    {
                        "type": sub_type,
                        "name": sub_name,
                        "options": [
                            {
                                "type": sub_group_type,
                                "name": sub_group_name,
                                "options": options,
                            }
                        ],
                    }
                ],
                "application_command": {
                    "id": command_info["id"],
                    "application_id": "270904126974590976",
                    "version": command_info["version"],
                    "default_permission": command_info["default_permission"],
                    "default_member_permissions": command_info["default_member_permissions"],
                    "type": command_info["type"],
                    "name": name,
                    "nsfw": command_info["nsfw"],
                    "description": command_info["description"],
                    "dm_permission": command_info["dm_permission"],
                    "options": command_info["options"],
                },
                "attachments": [],
            },
            "nonce": nonce,
        }
        def check(message: Message):
            return message.nonce == nonce

        for i in range(retry_attempts):
            response = requests.post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    json=data,
                    headers={"Authorization": self.token, "Content-type": "application/json"}
                )
            
            try:
                message: Optional[Union[Message, bool]] = self.wait_for("MESSAGE_CREATE", check=check, timeout=timeout)
                return message # type: ignore
            except Exception as e:
                print(f"Error in run_slash_group_command: {e}")
                continue
        
        return None

    def click(self, button: Button, retry_attempts: int = 10, timeout: int = 10) -> bool:
        """Clicks a button.
        
        Parameters
        --------
        button: Button
            The button to click.
        retry_attempts: int = 10
            The amount of times to retry on failure.
        timeout: int = 10
            Duration before it times out.

        Returns
        --------
        success_state: bool
            Whether the button was clicked successfully or not.
        """
        nonce = self._create_nonce()
        retry_attempts = retry_attempts if retry_attempts > 0 else 1
        data = {
            "type": 3,
            "nonce": nonce,
            "guild_id": str(self.guild_id),
            "channel_id": self.channel_id,
            "message_flags": 0,
            "message_id": button.message_id,
            "application_id": "270904126974590976",
            "session_id": self.session_id,
            "data": {"component_type": 2, "custom_id": button.custom_id},
        }
        end = time.time() + timeout
        for i in range(retry_attempts):
            if time.time() > end:
                return False
            response = requests.post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    json=data,
                    headers={"Authorization": self.token, "Content-type": "application/json"}
                )
            if response.status_code == 204:
                break
            retry_after = int(response.json().get('retry_after', 0))
            end += retry_after
            time.sleep(retry_after)
        
        return True if response.status_code == 204 else False # type: ignore

    def select(self, dropdown: Dropdown, options: list, retry_attempts: int = 10, timeout: int = 10) -> bool:
        """Selects an option from a dropdown.

        Parameters
        dropdown: Dropdown
            The dropdown to choose from.
        options: list
            A list of options to use in the API request for the dropdown to be chosen from.
        retry_attempts: int = 10
            The amount of times to retry on failure.
        timeout: int = 10
        --------
        dropdown: Dropdown
            The dropdown to choose from.
        options: list
            A list of options to use in the API request for the dropdown to be chosen from.
        retry_attempts: int = 10
            The amount of times to retry on failure.
        timeout: int = 10
            Duration before it times out.
        
        Returns
        -------
        success_state: bool
            Whether the option was chosen successfully or not.
        """
        nonce = self._create_nonce()
        data = {
            "type": 3,
            "nonce": nonce,
            "guild_id": str(self.guild_id),
            "channel_id": self.channel_id,
            "message_flags": 0,
            "message_id": dropdown.message_id,
            "application_id": "270904126974590976",
            "session_id": self.session_id,
            "data": {
                "component_type": 3,
                "custom_id": dropdown.custom_id,
                "type": 3,
                "values": options,
            },
        }

        end = time.time() + timeout
        for i in range(retry_attempts):
            if time.time() > end:
                return False
            response = requests.post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    json=data,
                    headers={"Authorization": self.token, "Content-type": "application/json"}
                )
            if response.status_code == 204:
                break
            retry_after = int(response.json().get('retry_after', 0))
            end += retry_after
            time.sleep(retry_after)
        
        return True if response.status_code == 204 else False # type: ignore

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
