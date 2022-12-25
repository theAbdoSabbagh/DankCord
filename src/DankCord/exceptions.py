class DankCordException(BaseException):
    pass


class InvalidCommand(DankCordException):
    pass


class InvalidComponent(DankCordException):
    pass


class InvalidToken(DankCordException):
    pass


class MissingPermissions(DankCordException):
    pass


class UnknownChannel(DankCordException):
    pass


class NonceTimeout(DankCordException):
    pass


class NoCommands(DankCordException):
    pass

class DataAccessFailure(DankCordException):
    pass