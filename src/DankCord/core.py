import orjson, datetime, json, time
import faster_than_requests as requests

from typing import Optional
from pyloggor import pyloggor

from .exceptions import InvalidComponent, UnknownChannel, NonceTimeout
from .Objects import Response, Config, Message

class Core:
    def __init__(self,
        /,
        config: Config,
        commands_data: dict,
        guild_id : Optional[int],
        session_id : Optional[str],
        logger: pyloggor
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

    def _tupalize(self, dict):
        return [(a, b) for a, b in dict.items()]

    def _create_nonce(self) -> str:
        return str(int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000 - 1420070400000) << 22)

    def _get_command_info(self, name: str) -> dict:
        if self.resource_intensivity == "MEM":
            return self.commands_data.get(name, {})
        else:
            return json.load(open(f"{self.channel_id}_commands.json")).get(name, {})

    def _run_command(self, name: str, retry_attempts= 3, timeout:int = 10):
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

    # Raw commands
    def fish(self, retry_attempts:int = 3, timeout:int = 10):
        self._run_command("fish", retry_attempts, timeout)
        
    def hunt(self, retry_attempts:int = 3, timeout:int = 10):
        self._run_command("hunt", retry_attempts, timeout)
        
    def dig(self, retry_attempts:int = 3, timeout:int = 10):
        self._run_command("dig", retry_attempts, timeout)
        
    def beg(self, retry_attempts:int = 3, timeout:int = 10):
        self._run_command("beg", retry_attempts, timeout)
    
    # Button commands
    def search(self, retry_attempts:int = 3, timeout:int = 10):
        self._run_command("search", retry_attempts, timeout)

    def crime(self, retry_attempts: int = 3, timeout:int = 10):
        self._run_command("crime", retry_attempts, timeout)

    def postmemes(self, retry_attempts: int = 3, timeout:int = 10):
        self._run_command("postmemes", retry_attempts, timeout)

    # Gamble commands
    def slots(self, retry_attempts: int = 3, timeout:int = 10):
        self._run_command("slots", retry_attempts, timeout)

    def gamble(self, retry_attempts: int = 3, timeout:int = 10):
        self._run_command("gamble", retry_attempts, timeout)

    def snakeeyes(self, retry_attempts: int = 3, timeout:int = 10):
        self._run_command("snakeeyes", retry_attempts, timeout)
