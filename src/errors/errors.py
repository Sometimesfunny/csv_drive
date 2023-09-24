class NoCredentialsException(Exception):
    def __init__(self) -> None:
        super().__init__("Not enough database credentials provided")


class UserAlreadyExists(Exception):
    def __init__(self, username: str) -> None:
        super().__init__(f"User with name {username} already exists")


class TokenExpiredException(Exception):
    def __init__(self) -> None:
        super().__init__("Token expired, please create new one")


class CSVValidationError(Exception):
    def __init__(self) -> None:
        super().__init__("Could not validate file")
