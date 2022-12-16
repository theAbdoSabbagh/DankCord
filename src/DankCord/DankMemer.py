from typing import Union

import faster_than_requests as requests

from .Objects import Config, Response


class PepeCaptcha:
    def __init__(self) -> None:
        pass


class EmojiCaptcha:
    def __init__(self) -> None:
        pass


class DankMemer:
    def __init__(self, config: Config) -> None:
        self.token = config.token

        self.emoji_ids = [
            819014822867894304,
            796765883120353280,
            860602697942040596,
            860602923665588284,
            860603013063507998,
            936007340736536626,
            933194488241864704,
            680105017532743700,
        ]

    @property
    def captcha_types(self) -> Union[PepeCaptcha, EmojiCaptcha]:
        return PepeCaptcha, EmojiCaptcha  # type: ignore

    @property
    def captcha_emojis(self) -> list:
        return self.emoji_ids

    def get_commands(self, channel_id: int) -> Response:
        response = Response(
            requests.get(  # type: ignore
                f"https://discord.com/api/v9/channels/{channel_id}/application-commands/search?type=1&application_id=270904126974590976",
                http_headers=[("Authorization", self.token)],
            )
        )
        return response
