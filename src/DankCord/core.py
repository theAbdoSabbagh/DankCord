import datetime, json, time
import requests

from typing import Optional, Literal, Union, Callable
from pyloggor import pyloggor
from random import randint

from .Objects import Config, Message, Parser
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
        cmd : Message = self.run_command("fish", retry_attempts, timeout)
        if Parser.check_cooldown(cmd.embeds[0].description):
            return Parser.cooldown(cmd.embeds[0].description)
        return Parser.common1(cmd.embeds[0].description)
        
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
        cmd : Message = self.run_command("hunt", retry_attempts, timeout)
        if Parser.check_cooldown(cmd.embeds[0].description):
            return Parser.cooldown(cmd.embeds[0].description)
        return Parser.common1(cmd.embeds[0].description)
        
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
        cmd : Message = self.run_command("dig", retry_attempts, timeout)
        if Parser.check_cooldown(cmd.embeds[0].description):
            return Parser.cooldown(cmd.embeds[0].description)
        return Parser.common1(cmd.embeds[0].description)
        
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
        cmd: Message = self.run_command("beg", retry_attempts, timeout)
        if Parser.check_cooldown(cmd.embeds[0].description):
            return Parser.cooldown(cmd.embeds[0].description)
        return Parser.beg(cmd.embeds[0].description)
    
    # Button commands
    def search(self, retry_attempts:int = 3, timeout:int = 10, location_index:Literal[1, 2, 3, "random"] = 2):
        """
        Runs the `search` command.
        
        Arguments
        --------
        retry_attempts: `int`
            The amount of times to retry when executing the command fails.
        timeout: `int`
            The time it waits for to confirm whether a command was ran or not.
        location_index: `Literal[1, 2, 3, "random"]`
            The location to search for.
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
        _location = None
        if location_index not in [1, 2, 3, "random"]:
            _location = "random"
        _location = location_index if location_index in [1, 2, 3, "random"] else randint(1, 3)
        cmd : Message = self.run_command("search", retry_attempts, timeout)
        if Parser.check_cooldown(cmd.embeds[0].description):
            return Parser.cooldown(cmd.embeds[0].description)
        self.click(cmd.buttons[_location - 1])
        def check(message):
            return message.channel_id == int(self.channel_id) and message.author.id == 270904126974590976 and "searched" in message.embeds[0].authorName
        cmd = self.wait_for("MESSAGE_UPDATE", check=check)
        return Parser.search(cmd.embeds[0].description)
        

    def crime(self, retry_attempts: int = 3, timeout:int = 10, location_index:Literal[1, 2, 3, "random"] = 2):
        """
        Runs the `crime` command.
        
        Arguments
        --------
        retry_attempts: `int`
            The amount of times to retry when executing the command fails.
        timeout: `int`
            The time it waits for to confirm whether a command was ran or not.
        location_index: `Literal[1, 2, 3, "random"]`
            The place to commit the crime in.
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
        _location = None
        if location_index not in [1, 2, 3, "random"]:
            _location = "random"
        _location = location_index if location_index in [1, 2, 3, "random"] else randint(1, 3)
        cmd : Message = self.run_command("crime", retry_attempts, timeout)
        if Parser.check_cooldown(cmd.embeds[0].description):
            return Parser.cooldown(cmd.embeds[0].description)
        self.click(cmd.buttons[_location - 1])
        def check(message):
            return message.author.id == 270904126974590976 and "committed" in message.embeds[0].authorName
        cmd = self.wait_for("MESSAGE_UPDATE", check=check)
        return Parser.crime(cmd.embeds[0].description)

    def postmemes(self, retry_attempts: int = 3, timeout:int = 10, platform:Literal["discord", "reddit", "twitter", "facebook", "random"] = "random", type:Literal["fresh", "repost", "intellectual", "copypasta", "kind", "random"] = "random"):
        """
        Runs the `postmemes` command.
        
        Arguments
        --------
        retry_attempts: `int`
            The amount of times to retry when executing the command fails.
        timeout: `int`
            The time it waits for to confirm whether a command was ran or not.
        platform: `Literal["discord", "reddit", "twitter", "facebook", "random"]`
            The platform to post the meme in.
        type: `Literal["fresh", "repost", "intellectual", "copypasta", "kind", "random"]`
            The type of meme to post.
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
        _platform = None
        _type = None
        if platform.lower() not in ["discord", "reddit", "twitter", "facebook"]:
            _platform = "random"
        else:
            _platform = ["discord", "reddit", "twitter", "facebook"].index(platform.lower())
        if type.lower() not in ["fresh", "repost", "intellectual", "copypasta", "kind"]:
            _type = "random"
        else:
            _type = ["fresh", "repost", "intellectual", "copypasta", "kind"].index(type.lower())
        _platform = _platform if not _platform == "random" else randint(0, 3)
        _type = _type if not _type == "random" else randint(0, 4)
        cmd : Message = self.run_command("postmemes", retry_attempts, timeout)
        if Parser.check_cooldown(cmd.embeds[0].description):
            return Parser.cooldown(cmd.embeds[0].description)
        def check(message):
            return message.channel_id == int(self.channel_id) and message.author.id == 270904126974590976 and "Meme Posting Session" in message.embeds[0].authorName and "**You" in message.embeds[0].description or "No one" in message.embeds[0].description or "Do you even" in message.embeds[0].description or "Your meme" in message.embeds[0].description or "your meme" in message.embeds[0].description
        self.select(cmd.dropdowns[0], [cmd.dropdowns[0].options[_platform].value])
        self.select(cmd.dropdowns[1], [cmd.dropdowns[1].options[_type].value])
        self.click(cmd.buttons[0])
        cmd = self.wait_for("MESSAGE_UPDATE", check=check)
        return Parser.postmemes(cmd.embeds[0].description)