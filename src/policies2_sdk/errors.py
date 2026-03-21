class SDKError(Exception):
    pass


class ConfigurationError(SDKError):
    pass


class TransportError(SDKError):
    pass


class AuthenticationError(SDKError):
    pass


class AuthorizationError(SDKError):
    pass


class ServerError(SDKError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status
