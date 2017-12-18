class ApiException(Exception):
    """
    All app specific exceptions inherit from this exception. Enables better
    handling and more meaningful http response message generation.
    """
    def __init__(self, message, status=500):
        super(ApiException, self).__init__(message)
        self.status = status


class NotFound(ApiException):
    pass


class Exists(ApiException):
    def __init__(self, message):
        super(Exists, self).__init__(message)
        self.status = 409


class NotAllowed(ApiException):
    def __init__(self, message):
        super(NotAllowed, self).__init__(message)
        self.status = 403
