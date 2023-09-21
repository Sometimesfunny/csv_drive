class NoCredentialsException(Exception):
    def __init__(self) -> None:
        super().__init__("Not enough database credentials provided.")
