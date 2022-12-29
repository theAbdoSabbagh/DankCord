import datetime, json, time
import requests

from typing import Optional, Literal, Union, Callable
from pyloggor import pyloggor

from .Objects import Config, Message
from .gateway import Gateway
from .api import API

class Core(API):
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

    # Raw commands
    def fish(self, retry_attempts: int = 3, timeout: int = 10):
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
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        message: Optional[Message] = self.run_command("fish", retry_attempts, timeout)
        return message
        
    def hunt(self, retry_attempts: int = 3, timeout: int = 10):
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
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        message: Optional[Message] = self.run_command("hunt", retry_attempts, timeout)
        return message
        
    def dig(self, retry_attempts: int = 3, timeout: int = 10):
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
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        message: Optional[Message] = self.run_command("dig", retry_attempts, timeout)
        return message
        
    def beg(self, retry_attempts: int = 3, timeout: int = 10):
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
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        message: Optional[Message] = self.run_command("beg", retry_attempts, timeout)
        return message
    
    # Button commands
    def search(self, retry_attempts: int = 3, timeout: int = 10):
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
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        message: Optional[Message] = self.run_command("search", retry_attempts, timeout)
        return message

    def crime(self, retry_attempts: int = 3, timeout: int = 10):
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
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        message: Optional[Message] = self.run_command("crime", retry_attempts, timeout)
        return message

    def postmemes(self, retry_attempts: int = 3, timeout: int = 10):
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
        UnknownChannel
            Bot doesn't have access to that channel.

        Returns
        --------
        message: Optional[`Message`]
        """
        message: Optional[Message] = self.run_command("postmemes", retry_attempts, timeout)
        return message
