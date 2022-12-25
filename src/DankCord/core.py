import orjson, datetime, json, time
import requests

from typing import Optional, Literal, Union, Callable
from pyloggor import pyloggor

from .Objects import Config, Message
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

    def _create_nonce(self) -> str:
        """Creates a nonce using Discord's algorithm.
        
        Returns
        --------
        nonce: str"""
        return str(int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000 - 1420070400000) << 22)

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

    def _run_command(self, name: str, retry_attempts: int = 3, timeout: int = 10, **kwargs) -> Optional[Message]:
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

        for item in command_info["options"]:
            if item["name"] == name:
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
                "type": 1,
                "options": self._OptionsBuilder(name, type_, **kwargs),
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
                    data=orjson.dumps(data),
                    headers={"Content-type": "application/json", 
                            "Authorization": self.token,
                            "Content-Type": "application/json",
                        }
                )
            
            try:
                interaction: Optional[Union[Message, bool]] = self.wait_for("MESSAGE_CREATE", check=check, timeout=timeout)
                return interaction # type: ignore
            except Exception as e:
                print(f"Error in run_command: {e}")
                continue
            
        return None

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
