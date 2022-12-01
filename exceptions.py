class DankCordException(BaseException):
  pass

class InvalidCommand(DankCordException):
  pass

class InvalidToken(DankCordException):
  pass

class UnknownChannel(DankCordException):
  pass