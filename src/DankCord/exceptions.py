class DankCordException(BaseException):
    pass


class InvalidToken(DankCordException):
    pass


class MissingPermissions(DankCordException):
    pass


class UnknownChannel(DankCordException):
    pass


class NoCommands(DankCordException):
    pass


class DataAccessFailure(DankCordException):
    pass


class InvalidFormBody(DankCordException):
    pass