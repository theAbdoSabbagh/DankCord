import datetime
import json
import time
import orjson
import faster_than_requests as requests

from string import printable
from threading import Thread
from typing import Optional
from rich import print

from .DankMemer import DankMemer
from .exceptions import NonceTimeout, UnknownChannel, InvalidComponent
from .gateway import Gateway
from .logger import Logger
from .Objects import Message, Response, Button, Dropdown


class Client:
    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.channel_id: str = channel_id

        self.logger = Logger()

        self.gateway = Gateway(self.token, self.channel_id, self.logger)

        self.ws = self.gateway.ws
        self.session_id: Optional[str] = self.gateway.session_id
        self.user_id: Optional[int] = self.gateway.user_id
        self.guild_id = self.gateway.guild_id

        self.ws_cache = {}

        self.dankmemer = DankMemer(self.token)
        self._get_commands()

        t1 = Thread(target=self._events_listener)
        t1.daemon = True
        t1.start()

    def _strip(self, content: str) -> str:
        return "".join([char for char in content if char in printable])

    def _tupalize(self, dict):
        return [(a, b) for a, b in dict.items()]

    def _create_nonce(self) -> str:
        return str(
            int(
                datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000
                - 1420070400000
            )
            << 22
        )

    def _get_commands(self, channel_id: Optional[str] = None) -> Optional[Response]:
        channel_id = channel_id or self.channel_id
        response = self.dankmemer.get_commands(int(channel_id))

        if isinstance(response, str):
            return response

        if response.data.get("code") == 10003:
            raise UnknownChannel("Bot doesn't have access to this channel.")

        if "application_commands" not in response.data:
            return response

        with open(f"{self.channel_id}_commands.json", "w") as f:
            json.dump(
                {
                    command_data["name"]: command_data
                    for command_data in response.data["application_commands"]
                },
                f,
                indent=4,
                sort_keys=True,
            )

        return response

    def _get_command_info(self, name: str) -> dict:
        return json.load(open(f"{self.channel_id}_commands.json")).get(name, {})

    def _events_listener(self):
        while True:
            m = self.ws.recv()
            if not m:
                continue
            event = orjson.loads(m)
            if not event or not event["d"] or not event["t"]:
                continue
            if "channel_id" not in event["d"]:
                continue
            if event["t"] not in ("MESSAGE_CREATE", "MESSAGE_UPDATE"):
                continue
            if (
                event["d"]["channel_id"] == self.channel_id
                or event["d"]["channel_id"] == "270904126974590976"
            ):
                if not "nonce" in event["d"].keys():
                    self.ws_cache[event["d"]["id"] + " " + event["t"]] = event["d"]
                else:
                    if not event["d"]["nonce"] in self.ws_cache:
                        self.ws_cache[event["d"]["nonce"]] = {}
                    self.ws_cache[event["d"]["nonce"]][event["t"]] = event["d"]

    def _OptionsBuilder(self, name, type_, **kwargs):
        options = [{"type": type_, "name": name, "options": []}]

        type_types = {str: 3, bool: 5, list: 2, int: 10}

        option_type = 3
        for key, value in kwargs.items():
            option_type = type_types[type(value)]
            new_piece_of_data = {"type": option_type,
                                 "name": key, "value": value}
            options[0]["options"].append(new_piece_of_data)

        return options

    def _RawOptionsBuilder(self, **kwargs):
        options = []

        type_types = {str: 3, bool: 5, list: 2, int: 10}

        option_type = 3
        for key, value in kwargs.items():
            option_type = type_types[type(value)]
            new_piece_of_data = {"type": option_type,
                                 "name": key, "value": value}
            options.append(new_piece_of_data)

        return options

    def get_info(self) -> Response:
        return Response(
            requests.get(  # type: ignore
                url="https://discord.com/api/v10/users/@me",
                http_headers=self._tupalize({"Authorization": self.token}),
            )
        )

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
                    "default_member_permissions": command_info[
                        "default_member_permissions"
                    ],
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
            post_handling = self._post_handling(
                timeout, response, name, nonce, ["MESSAGE_CREATE"]
            )
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
                    "default_member_permissions": command_info[
                        "default_member_permissions"
                    ],
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
            post_handling = self._post_handling(
                timeout, response, name, nonce, ["MESSAGE_CREATE"]
            )
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
                        ]
                    }
                ],
                "application_command": {
                    "id": command_info["id"],
                    "application_id": "270904126974590976",
                    "version": command_info["version"],
                    "default_permission": command_info["default_permission"],
                    "default_member_permissions": command_info[
                        "default_member_permissions"
                    ],
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
            post_handling = self._post_handling(
                timeout, response, name, nonce, ["MESSAGE_CREATE"]
            )
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
        message_id: str = ""
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
                    self.logger.ratelimit(
                        retry_after=retry_after, command_name=name)
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
                        if value["message_reference"]["message_id"].strip() == message_id.strip and value["type"] == 19 and event in event_type:
                            _message = value
                            return Message(_message)
                    except Exception as e:
                        pass
            except:
                pass

        if not _message:
            raise NonceTimeout("Did not receive nonce in time.")

        return None
    
    def click(self, button: Button, retry_attempts: int=10, timeout: int=10) -> Optional[Message]:
        nonce = self._create_nonce()
        data = {
            "type": 3,
            "nonce": nonce,
            "guild_id": str(self.guild_id),
            "channel_id": self.channel_id,
            "message_flags": 0,
            "message_id": button.message_id,
            "application_id": "270904126974590976",
            "session_id": self.session_id,
            "data": {
                "component_type": 2,
                "custom_id": button.custom_id
            }
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
                timeout, response, "button interactions", nonce, ["MESSAGE_CREATE", "MESSAGE_UPDATE"], message_id=button.message_id
            )
            if post_handling:
                return post_handling
            continue
    
    def select(self, dropdown: Dropdown, options: list, retry_attempts: int=10, timeout: int=10) -> Optional[Message]:
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
                "values": options
            }
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
                timeout, response, "dropdown interactions", nonce, ["MESSAGE_CREATE", "MESSAGE_UPDATE"], message_id=dropdown.message_id
            )
            if post_handling:
                return post_handling
            continue
