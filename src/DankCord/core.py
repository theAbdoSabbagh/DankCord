import orjson, datetime, json, time
import faster_than_requests as requests

from typing import Optional, Literal, Union
from pyloggor import pyloggor
from websocket import WebSocket

from .Objects import Response, Config, Message
from .gateway import Gateway

class Core:
    def __init__(self,
        /,
        config: Config,
        commands_data: dict,
        guild_id : Optional[int],
        session_id : Optional[str],
        logger: pyloggor,
        gateway: Gateway
    ) -> None:
        self.token = config.token
        self.channel_id = config.channel_id
        self.dm_mode = config.dm_mode
        self.resource_intensivity = config.resource_intensivity
        self.session_id = session_id
        self.commands_data = commands_data
        self.guild_id = guild_id
        self.logger = logger
        self.ws_cache = {}
        self.gateway = gateway

    def _tupalize(self, dict):
        return [(a, b) for a, b in dict.items()]

    def _create_nonce(self) -> str:
        return str(int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000 - 1420070400000) << 22)

    def _get_command_info(self, name: str) -> dict:
        if self.resource_intensivity == "MEM":
            return self.commands_data.get(name, {})
        else:
            return json.load(open(f"{self.channel_id}_commands.json", "r+")).get(name, {})

    def _run_command(self, name: str, retry_attempts= 3, timeout:int = 10) -> Optional[Message]:
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
            try:
                interaction: Optional[Union[Message, bool]] = self.wait_for("MESSAGE_CREATE", nonce, timeout)
                return interaction # type: ignore
            except Exception as e:
                print(f"Error in core.py _run_command: {e}")
                continue
            
        return None

    def wait_for(
        self,
        event: Literal["MESSAGE_CREATE", "MESSAGE_UPDATE", "INTERACTION_CREATE", "INTERACTION_SUCCESS"],
        nonce_or_id: str,
        timeout: int = 10
    ) -> Optional[Union[Message, bool]]:
        limit = time.time() + timeout
        while time.time() < limit:
            cache = self.gateway.cache
            if event in ("INTERACTION_CREATE", "INTERACTION_SUCCESS"):
                if nonce_or_id in cache.interaction_create or nonce_or_id in cache.interaction_success:
                    return True
            if event == "MESSAGE_CREATE":
                if cache.message_create.get(nonce_or_id):
                    return Message(cache.message_create[nonce_or_id])
            if event == "MESSAGE_UPDATE":
                if cache.message_updates.get(nonce_or_id):
                    return Message(cache.message_updates[nonce_or_id])
        return None

    # Raw commands
    def fish(self, retry_attempts:int = 3, timeout:int = 10):
        """
        Runs the `fish` command.
        
        Arguments
        --------
        retry_attempts: `int`
            The amount of times to retry when executing the command fails.
        timeout: `int`
            The time it waits for to confirm whether a command was ran or not.
        
        Raises
        --------
        InvalidComponent
            invalidcomponentdescription
        NonceTimeout
            Couldn't get the nonce from the Websocket.
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        return self._run_command("fish", retry_attempts, timeout)
        
    def hunt(self, retry_attempts:int = 3, timeout:int = 10):
        """
        Runs the `hunt` command.
        
        Arguments
        --------
        retry_attempts: `int`
            The amount of times to retry when executing the command fails.
        timeout: `int`
            The time it waits for to confirm whether a command was ran or not.
        
        Raises
        --------
        InvalidComponent
            invalidcomponentdescription
        NonceTimeout
            Couldn't get the nonce from the Websocket.
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        return self._run_command("hunt", retry_attempts, timeout)
        
    def dig(self, retry_attempts:int = 3, timeout:int = 10):
        """
        Runs the `dig` command.
        
        Arguments
        --------
        retry_attempts: `int`
            The amount of times to retry when executing the command fails.
        timeout: `int`
            The time it waits for to confirm whether a command was ran or not.
        
        Raises
        --------
        InvalidComponent
            invalidcomponentdescription
        NonceTimeout
            Couldn't get the nonce from the Websocket.
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        return self._run_command("dig", retry_attempts, timeout)
        
    def beg(self, retry_attempts:int = 3, timeout:int = 10):
        """
        Runs the `beg` command.
        
        Arguments
        --------
        retry_attempts: `int`
            The amount of times to retry when executing the command fails.
        timeout: `int`
            The time it waits for to confirm whether a command was ran or not.
        
        Raises
        --------
        InvalidComponent
            invalidcomponentdescription
        NonceTimeout
            Couldn't get the nonce from the Websocket.
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        return self._run_command("beg", retry_attempts, timeout)
    
    # Button commands
    def search(self, retry_attempts:int = 3, timeout:int = 10):
        """
        Runs the `search` command.
        
        Arguments
        --------
        retry_attempts: `int`
            The amount of times to retry when executing the command fails.
        timeout: `int`
            The time it waits for to confirm whether a command was ran or not.
        
        Raises
        --------
        InvalidComponent
            invalidcomponentdescription
        NonceTimeout
            Couldn't get the nonce from the Websocket.
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        return self._run_command("search", retry_attempts, timeout)

    def crime(self, retry_attempts: int = 3, timeout:int = 10):
        """
        Runs the `crime` command.
        
        Arguments
        --------
        retry_attempts: `int`
            The amount of times to retry when executing the command fails.
        timeout: `int`
            The time it waits for to confirm whether a command was ran or not.
        
        Raises
        --------
        InvalidComponent
            invalidcomponentdescription
        NonceTimeout
            Couldn't get the nonce from the Websocket.
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        return self._run_command("crime", retry_attempts, timeout)

    def postmemes(self, retry_attempts: int = 3, timeout:int = 10):
        """
        Runs the `postmemes` command.
        
        Arguments
        --------
        retry_attempts: `int`
            The amount of times to retry when executing the command fails.
        timeout: `int`
            The time it waits for to confirm whether a command was ran or not.
        
        Raises
        --------
        InvalidComponent
            invalidcomponentdescription
        NonceTimeout
            Couldn't get the nonce from the Websocket.
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        return self._run_command("postmemes", retry_attempts, timeout)
