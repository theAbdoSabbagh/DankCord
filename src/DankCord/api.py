from typing import Optional, Union
from time import time, sleep
from datetime import datetime, timezone

from requests import post
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError

from .exceptions import InvalidFormBody
from .Objects import Message, Button, Dropdown

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
        command_info = self._get_command_info(name) # type: ignore

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
            "guild_id": str(self.guild_id), # type: ignore
            "channel_id": self.channel_id, # type: ignore
            "session_id": self.session_id, # type: ignore
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
            response = post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    json=data,
                    headers={"Authorization": self.token, "Content-type": "application/json"} # type: ignore
                )
            
            try:
                response_data = response.json()
                _errors: dict = response_data.get("errors", {}).get("data", {}).get("values", {}).get("0", {}).get("_errors", {})
                if _errors.get("message"):
                    raise InvalidFormBody(_errors.get("message"))
            except RequestsJSONDecodeError:
                pass

            try:
                interaction: Optional[Union[Message, bool]] = self.wait_for("MESSAGE_CREATE", check=check, timeout=timeout)  # type: ignore
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
        command_info = self._get_command_info(name) # type: ignore
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
            "guild_id": str(self.guild_id), # type: ignore
            "channel_id": self.channel_id, # type: ignore
            "session_id": self.session_id, # type: ignore
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
            response = post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    json=data,
                    headers={"Authorization": self.token, "Content-type": "application/json"} # type: ignore
                )

            try:
                response_data = response.json()
                _errors: dict = response_data.get("errors", {}).get("data", {}).get("values", {}).get("0", {}).get("_errors", {})
                if _errors.get("message"):
                    raise InvalidFormBody(_errors.get("message"))
            except RequestsJSONDecodeError:
                pass
            
            try:
                message: Optional[Union[Message, bool]] = self.wait_for("MESSAGE_CREATE", check=check, timeout=timeout) # type: ignore
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
        command_info = self._get_command_info(name) # type: ignore
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
            response = post(  # type: ignore
                    "https://discord.com/api/v9/interactions",
                    json=data,
                    headers={"Authorization": self.token, "Content-type": "application/json"} # type: ignore
                )
                
            try:
                response_data = response.json()
                _errors: dict = response_data.get("errors", {}).get("data", {}).get("values", {}).get("0", {}).get("_errors", {})
                if _errors.get("message"):
                    raise InvalidFormBody(_errors.get("message"))
            except RequestsJSONDecodeError:
                pass
            
            try:
                message: Optional[Union[Message, bool]] = self.wait_for("MESSAGE_CREATE", check=check, timeout=timeout) # type: ignore
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
                
            try:
                response_data = response.json()
                _errors: dict = response_data.get("errors", {}).get("data", {}).get("values", {}).get("0", {}).get("_errors", {})
                if _errors.get("message"):
                    raise InvalidFormBody(_errors.get("message"))
            except RequestsJSONDecodeError:
                pass

            if response.status_code == 204:
                break
            retry_after = int(response.json().get('retry_after', 0))
            end += retry_after
            sleep(retry_after)
        
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
                "values": options,
            },
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
                
            try:
                response_data = response.json()
                _errors: dict = response_data.get("errors", {}).get("data", {}).get("values", {}).get("0", {}).get("_errors", {})
                if _errors.get("message"):
                    raise InvalidFormBody(_errors.get("message"))
            except RequestsJSONDecodeError:
                pass

            if response.status_code == 204:
                break
            retry_after = int(response.json().get('retry_after', 0))
            end += retry_after
            sleep(retry_after)
        
        return True if response.status_code == 204 else False # type: ignore
