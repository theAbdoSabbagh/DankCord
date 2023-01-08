from typing import Optional, Union
from time import time, sleep
from datetime import datetime, timezone

from rich import print
from requests import post
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError

from .exceptions import InvalidFormBody
from .objects import Message, Button, Dropdown

class API:
    """A class that has some useful commands related to communicating with the Discord API."""
    def __init__(self) -> None:
        pass

    def _create_nonce(self) -> str:
        """Creates a nonce using Discord's algorithm.
        
        Returns
        --------
        nonce: str"""
        return str(int(datetime.now(timezone.utc).timestamp() * 1000 - 1420070400000) << 22)

    def _RawOptionsBuilder(
        self,
        options: dict,
        **kwargs
    ):
        """Builds the raw data used in slash command API requests.

        Parameters
        --------
        kwargs: **kwargs

        Returns
        --------
        options: list
        """
        options_ = []

        option_type = 3
        for key, value in kwargs.items():
            for option in options:
                # print(f"Option: {option} - Name: {option['name']} - Check: {key.lower() == option['name'].lower()} - Key: {key} - Value: {value}")
                if option["name"].lower() == key.lower():
                    option_type = option["type"]
                    # print(f"{key}: {option_type}")
            new_piece_of_data = {"type": option_type, "name": key, "value": value}
            options_.append(new_piece_of_data)

        return options_

    def run_command(
        self,
        name: str,
        retry_attempts: int = 3,
        timeout: int = 10,
        **kwargs
    ) -> Optional[Message]:
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
        command_info: dict = self._get_command_info(name) # type: ignore

        retry_attempts = retry_attempts if retry_attempts > 0 else 1
        type_ = command_info.get('type')
        options = []

        if command_info.get("options"):
            for item in command_info["options"]:
                if item["name"] == name:
                    type_ = item["type"]
                    break
            if len(kwargs) > 0:
                options = self._RawOptionsBuilder(command_info["options"], **kwargs)

        data = {
            "type": 2,
            "application_id": "270904126974590976",
            "guild_id": str(self.guild_id), # type: ignore
            "channel_id": self.channel_id, # type: ignore
            "session_id": self.session_id, # type: ignore
            "data": {
                "version": command_info["version"],
                "id": command_info["id"],
                "name": name,
                "type": type_,
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
            response = post( # type: ignore
                "https://discord.com/api/v9/interactions",
                json=data,
                headers={"Authorization": self.token, "Content-type": "application/json"} # type: ignore
            )
                
            try:
                response_data = response.json()
            except RequestsJSONDecodeError:
                response_data = {}
            
            if response_data.get("retry_after"):
                sleep(response_data["retry_after"])
                continue

            _errors_data: dict = response_data.get("errors", {}).get("data", {})
            error = None
            for line in str(_errors_data).splitlines():
                if not 'message' in line:
                    continue
                error = line.split("'message': ")[-1].replace("'", "").split('}')[0]

            if error:
                raise InvalidFormBody(error)

            try:
                interaction: Optional[Union[Message, bool]] = self.wait_for("MESSAGE_CREATE", check=check, timeout=timeout)  # type: ignore
                return interaction # type: ignore
            except Exception as e:
                print(f"Error in run_command: {e}")
                continue
        
        return None

    def run_sub_command(
        self,
        name: str,
        sub_name: str,
        retry_attempts: int = 3,
        timeout: int = 10,
        **kwargs
    ) -> Optional[Message]:
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
        command_info = self._get_command_info(name) # type: ignore
        retry_attempts = retry_attempts if retry_attempts > 0 else 1
        type_ = 1
        options = []

        if command_info.get("options"):
            for item in command_info["options"]:
                if item["name"] == name:
                    type_ = item["type"]
                    break
            options = self._RawOptionsBuilder(command_info["options"], **kwargs)

        data = {
            "type": 2,
            "application_id": "270904126974590976",
            "guild_id": str(self.guild_id), # type: ignore
            "channel_id": self.channel_id, # type: ignore
            "session_id": self.session_id, # type: ignore
            "data": {
                "version": command_info["version"],
                "id": command_info["id"],
                "name": name,
                "type": command_info["type"],
                "options": [
                    {
                        "type": type_,
                        "name": sub_name,
                        "options": options
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
            response = post( # type: ignore
                "https://discord.com/api/v9/interactions",
                json=data,
                headers={"Authorization": self.token, "Content-type": "application/json"} # type: ignore
            )

            try:
                response_data = response.json()
            except RequestsJSONDecodeError:
                response_data = {}
            
            if response_data.get("retry_after"):
                sleep(response_data["retry_after"])
                continue

            _errors_data: dict = response_data.get("errors", {}).get("data", {})
            error = None
            for line in str(_errors_data).splitlines():
                if not 'message' in line:
                    continue
                error = line.split("'message': ")[-1].replace("'", "").split('}')[0]

            if error:
                raise InvalidFormBody(error)

            try:
                message: Optional[Union[Message, bool]] = self.wait_for("MESSAGE_CREATE", check=check, timeout=timeout) # type: ignore
                return message # type: ignore
            except Exception as e:
                print(f"Error in run_sub_command: {e}")
                continue
        
        return None

    def run_slash_group_command(
        self,
        name: str,
        sub_name: str,
        sub_group_name: str,
        retry_attempts: int = 3,
        timeout: int = 10,
        **kwargs
    ) -> Optional[Message]:
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
        message: Optional[`Message`]"""

        nonce = self._create_nonce()
        command_info = self._get_command_info(name) # type: ignore
        retry_attempts = retry_attempts if retry_attempts > 0 else 1
        sub_type = 1
        sub_group_type = 1
        options = []

        for item in command_info.get("options", []): # Main cmd data
            if item.get("name") == sub_name:
                sub_type = item.get("type", sub_type)
                for item_ in item.get("options", []): # Sub command data
                    if item_.get("name") == sub_group_name:
                        # print(item.get('name'), item_.get('name'), sub_group_name, item_.get('type'), sub_group_type)
                        sub_group_type = item_.get("type", sub_group_type)
        first_index = [index for index, item in enumerate(command_info.get('options', []))
        if 'options' in item.keys() and item['name'] == sub_name][0]
        second_index = [index for index, item in enumerate(command_info.get('options', [])[first_index].get('options', []))
        if item['name'] == sub_group_name][0]
        if command_info.get("options", [])[first_index].get("options")[second_index].get("options") is not None:
            options = self._RawOptionsBuilder(
                command_info.get("options", [])[first_index].get("options")[second_index].get("options"),
                **kwargs
            )

        data = {
            "type": 2,
            "application_id": "270904126974590976",
            "guild_id": str(self.guild_id), # type: ignore
            "channel_id": self.channel_id, # type: ignore
            "session_id": self.session_id, # type: ignore
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
            response = post( # type: ignore
                "https://discord.com/api/v9/interactions",
                json=data,
                headers={"Authorization": self.token, "Content-type": "application/json"} # type: ignore
            )

            try:
                response_data = response.json()
            except RequestsJSONDecodeError:
                response_data = {}
            # else:
                # print(response_data)

            _errors_data: dict = response_data.get("errors", {}).get("data", {})
            error = None
            for line in str(_errors_data).splitlines():
                if not 'message' in line:
                    continue
                error = line.split("'message': ")[-1].replace("'", "").split('}')[0]

            if error:
                raise InvalidFormBody(error)

            if response_data.get("retry_after"):
                sleep(response_data["retry_after"])
                continue

            try:
                message: Optional[Union[Message, bool]] = self.wait_for("MESSAGE_CREATE", check=check, timeout=timeout) # type: ignore
                return message # type: ignore
            except Exception as e:
                print(f"Error in run_slash_group_command: {e}")
                continue
        
        return None

    def click(
        self,
        button: Button,
        retry_attempts: int = 10,
        timeout: int = 10
    ) -> bool:
        """Clicks a button.
        
        Parameters
        --------
        button: Button
            The button to click.
        retry_attempts: int = 10
            The amount of times to retry on failure.
        timeout: int = 10
            Duration before it times out.

        Raises
        --------
        InvalidFormBody
            Invalid form body.

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
            "guild_id": str(self.guild_id), # type: ignore
            "channel_id": self.channel_id, # type: ignore
            "message_flags": 0,
            "message_id": button.message_id,
            "application_id": "270904126974590976",
            "session_id": self.session_id, # type: ignore
            "data": {"component_type": 2, "custom_id": button.custom_id},
        }

        end = time() + timeout
        for i in range(retry_attempts):
            if time() > end:
                return False

            response = post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    json=data,
                    headers={"Authorization": self.token, "Content-type": "application/json"} # type: ignore
                )

            if response.status_code == 204:
                break

            try:
                response_data = response.json()
            except RequestsJSONDecodeError:
                response_data = {}

            _errors: list[dict] = response_data.get("errors", {}).get("data", {}).get("_errors", {})
            retry_after = response_data.get("retry_after")
            if retry_after is not None:
                sleep(retry_after)
                continue

            if len(_errors) > 0 and _errors[0].get("message"):
                raise InvalidFormBody(_errors[0].get("message"))

        return True if response.status_code == 204 else False # type: ignore

    def select(
        self,
        dropdown: Dropdown,
        values_indexes: list,
        retry_attempts: int = 10,
        timeout: int = 10
    ) -> bool:
        """Selects an option from a dropdown.

        Parameters
        --------
        dropdown: Dropdown
            The dropdown to choose from.
        values_indexes: list
            A list of indexes of the options in the dropdown to choose.
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
            "guild_id": str(self.guild_id), # type: ignore
            "channel_id": self.channel_id, # type: ignore
            "message_flags": 0,
            "message_id": dropdown.message_id,
            "application_id": "270904126974590976",
            "session_id": self.session_id, # type: ignore
            "data": {
                "component_type": 3,
                "custom_id": dropdown.custom_id,
                "type": 3,
                "values": values_indexes,
            },
        }

        end = time() + timeout
        for i in range(retry_attempts):
            if time() > end:
                return False

            response = post( # type: ignore
                "https://discord.com/api/v9/interactions",
                json=data,
                headers={"Authorization": self.token, "Content-type": "application/json"} # type: ignore
            )
                
            if response.status_code == 204:
                break

            try:
                response_data = response.json()
            except RequestsJSONDecodeError:
                response_data = {}

            _errors: list[dict] = response_data.get("errors", {}).get("data", {}).get("_errors", {})
            retry_after = response_data.get("retry_after")
            if retry_after is not None:
                sleep(retry_after)
                continue

            if len(_errors) > 0 and _errors[0].get("message"):
                raise InvalidFormBody(_errors[0].get("message"))
        
        return True if response.status_code == 204 else False # type: ignore
