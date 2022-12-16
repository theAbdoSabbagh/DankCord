import datetime, json, time, orjson
import faster_than_requests as requests

from rich import print
from string import printable
from typing import Callable, Literal, Optional, Union
from pyloggor import pyloggor
from threading import Thread

from .DankMemer import DankMemer
from .exceptions import InvalidComponent, MissingPermissions, NoCommands, NonceTimeout, UnknownChannel
from .gateway import Gateway
from .Objects import Button, Config, Dropdown, Message, Response
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

        self.user_id: Optional[int] = self.gateway.user_id
        if not config.dm_mode:
            self.guild_id = self.gateway.guild_id

        self.dankmemer = DankMemer(config)
        self._get_commands()
        self._get_info()

        logger.log(
            level="Info", msg=f"Fully booted up, it took total {round(time.perf_counter() - __boot_start, 3)} seconds."
        )
        self.core = Core(config, self.commands_data, self.guild_id, self.session_id, self.logger, self.gateway)

    def _clean(self, content: str) -> str:
        return "".join([char for char in content if char in printable])

    def _tupalize(self, dict):
        return [(a, b) for a, b in dict.items()]

    def _create_nonce(self) -> str:
        return str(int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000 - 1420070400000) << 22)

    def _get_commands(self, channel_id: Optional[str] = None) -> Optional[Response]:
        channel_id = channel_id or self.channel_id
        response = self.dankmemer.get_commands(int(channel_id))

        if isinstance(response, str):
            return response

        if response.data.get("code") == 10003:
            raise UnknownChannel("Bot doesn't have access to this channel.")
        if response.data.get("code") == 50013:
            raise MissingPermissions("Bot cannot view the channel or read it's content.")

        if "application_commands" not in response.data:
            raise NoCommands("No commands found.")

        if self.resource_intensivity == "MEM":
            self.commands_data = {
                command_data["name"]: command_data for command_data in response.data["application_commands"]
            }
        else:
            with open(f"{self.channel_id}_commands.json", "w") as f:
                json.dump(
                    {command_data["name"]: command_data for command_data in response.data["application_commands"]},
                    f,
                    indent=4,
                    sort_keys=True,
                )

        return response

    def _get_command_info(self, name: str) -> dict:
        if self.resource_intensivity == "MEM":
            return self.commands_data.get(name, {})
        else:
            return json.load(open(f"{self.channel_id}_commands.json", "r+")).get(name, {})

    def _OptionsBuilder(self, name, type_, **kwargs):
        options = [{"type": type_, "name": name, "options": []}]

        type_types = {str: 3, bool: 5, list: 2, int: 10}

        option_type = 3
        for key, value in kwargs.items():
            option_type = type_types[type(value)]
            new_piece_of_data = {"type": option_type, "name": key, "value": value}
            options[0]["options"].append(new_piece_of_data)

        return options

    def _RawOptionsBuilder(self, **kwargs):
        options = []

        type_types = {str: 3, bool: 5, list: 2, int: 10}

        option_type = 3
        for key, value in kwargs.items():
            option_type = type_types[type(value)]
            new_piece_of_data = {"type": option_type, "name": key, "value": value}
            options.append(new_piece_of_data)

        return options

    def _get_info(self) -> None:
        resp = Response(
            requests.get(  # type: ignore
                url="https://discord.com/api/v10/users/@me",
                http_headers=self._tupalize({"Authorization": self.token}),
            )
        )
        if resp.code != 200:
            raise Exception("Failed to get user info.")
        self.username = resp.data["username"]

    def run_command(self, name: str, retry_attempts=3, timeout: int = 10):
        nonce = self._create_nonce()
        command_info = self._get_command_info(name)

        retry_attempts = retry_attempts if retry_attempts > 0 else 1

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
                "options": [],
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

        for i in range(retry_attempts):
            response = Response(
                requests.post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    orjson.dumps(data),
                    http_headers=self._tupalize(
                        {
                            "Authorization": self.token,
                            "Content-Type": "application/json",
                        }
                    ),
                )
            )
            post_handling = self._post_handling(timeout, response, name, nonce, ["MESSAGE_CREATE"])
            if post_handling:
                return post_handling
            continue

    def run_sub_command(
        self,
        name: str,
        sub_name: str,
        retry_attempts=3,
        timeout: int = 10,
        **kwargs,
    ):

        nonce = self._create_nonce()
        command_info = self._get_command_info(name)
        retry_attempts = retry_attempts if retry_attempts > 0 else 1
        type_ = 1

        for item in command_info["options"]:
            if item["name"] == sub_name:
                type_ = item["type"]
                break

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
                "options": self._OptionsBuilder(sub_name, type_, **kwargs),
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

        for i in range(retry_attempts):
            response = Response(
                requests.post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    orjson.dumps(data),
                    http_headers=[
                        ("Authorization", self.token),
                        ("Content-Type", "application/json"),
                    ],
                )
            )
            post_handling = self._post_handling(timeout, response, name, nonce, ["MESSAGE_CREATE"])
            if post_handling:
                return post_handling
            continue

    def run_slash_group_command(
        self,
        name: str,
        sub_name: str,
        sub_group_name: str,
        retry_attempts=3,
        timeout: int = 10,
        **kwargs,
    ):
        nonce = self._create_nonce()
        command_info = self._get_command_info(name)
        retry_attempts = retry_attempts if retry_attempts > 0 else 1
        sub_type = 1
        sub_group_type = 1

        for item in command_info["options"]:
            if item["name"] == sub_name:
                sub_type = item["type"]
            for item_ in item["options"]:
                if item_["name"] == sub_group_name:
                    sub_group_type = item_["type"]

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
                                "options": self._RawOptionsBuilder(**kwargs),
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

        for i in range(retry_attempts):
            response = Response(
                requests.post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    orjson.dumps(data),
                    http_headers=[
                        ("Authorization", self.token),
                        ("Content-Type", "application/json"),
                    ],
                )
            )
            post_handling = self._post_handling(timeout, response, name, nonce, ["MESSAGE_CREATE"])
            if post_handling:
                return post_handling
            continue

    def _post_handling(
        self,
        timeout: int,
        response: Response,
        name: str,
        nonce: str,
        event_type: list,
        message_id: str = "",
    ) -> Optional[Message]:
        _message = None

        if isinstance(response.data, dict):
            retry_after = int(response.data.get("retry_after", 0))
            errors = response.data.get("errors")
            code = response.data.get("code")
            if errors:
                # TODO horrible way, sometimes the error does NOT have data, so this needs fixing
                if response.data["errors"]["data"]["_errors"][0]["code"] == "COMPONENT_VALIDATION_FAILED":
                    raise InvalidComponent("Invalid component.")
                if retry_after > 0:
                    self.logger.log(level="Warning", msg=f"Ratelimited while running {name}, retrying after {retry_after}")
                    time.sleep(retry_after)

                return None
            if code == 10003:
                raise UnknownChannel("Bot doesn't have access to this channel.")

        lim = time.time() + timeout
        if message_id == "":
            while time.time() < lim:
                if nonce in self.ws_cache:
                    for i in event_type:
                        if i in self.ws_cache[nonce]:
                            _message = self.ws_cache[nonce][i]
                            return Message(_message)

        if not _message and message_id == "":
            raise NonceTimeout("Did not receive nonce in time.")

        lim = time.time() + timeout
        while time.time() < lim:
            try:
                for key, value in self.ws_cache.items():
                    try:
                        event = key.split(" ")[1]
                        if value["id"].strip() == message_id.strip() and event in event_type:
                            _message = value
                            return Message(_message)
                        if (
                            value["message_reference"]["message_id"].strip() == message_id.strip
                            and value["type"] == 19
                            and event in event_type
                        ):
                            _message = value
                            return Message(_message)
                    except Exception as e:
                        pass
            except:
                pass

        if not _message:
            raise NonceTimeout("Did not receive nonce in time.")

        return None

    def click(self, button: Button, retry_attempts: int = 10, timeout: int = 10) -> bool:
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
        for i in range(retry_attempts):
            response = Response(
                requests.post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    orjson.dumps(data),
                    http_headers=self._tupalize(
                        {
                            "Authorization": self.token,
                            "Content-Type": "application/json",
                        }
                    ),
                )
            )
            if response.code == 204:
                break
            time.sleep(int(response.data.get('retry_after', 0)))
        
        return True if response.code == 204 else False # type: ignore

    def select(
        self,
        dropdown: Dropdown,
        options: list,
        retry_attempts: int = 10,
        timeout: int = 10,
    ) -> Optional[Message]:
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
        for i in range(retry_attempts):
            response = Response(
                requests.post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    orjson.dumps(data),
                    http_headers=self._tupalize(
                        {
                            "Authorization": self.token,
                            "Content-Type": "application/json",
                        }
                    ),
                )
            )
            post_handling = self._post_handling(
                timeout,
                response,
                "dropdown interactions",
                nonce,
                ["MESSAGE_CREATE", "MESSAGE_UPDATE"],
                message_id=dropdown.message_id,
            )
            if post_handling:
                return post_handling

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

        The ``timeout`` parameter specifies how long to wait for until the desired event
        is dispatched; if the event was not dispatched before the timeout duration is over,
        it returns `None`.

        This function returns the **first event that meets the requirements**.

        Examples
        ---------

        Waiting for a message to be sent: ::

            def DankMemerShop():
                def check(message: Message):
                    # The author ID is the ID of Dank Memer
                    return message.author.id == 270904126974590976 and "shop" in message.embeds[0].title.lower()
                
                message = bot.wait_for("MESSAGE_CREATE", check = check)
                # in this case the message is of the type `Message`


        Parameters
        ------------
        event: :class:`str`
            The event name.
        check: Optional[Callable[..., :class:`bool`]]
            A predicate to check what to wait for. The arguments must meet the
            parameters of the event being waited for.
        timeout: Optional[:class:`float`]
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
