class IdeaGenerationError(Exception):
    """Raised when idea generation fails at the application level."""


class ProviderError(Exception):
    """Raised when the AI provider returns an unexpected or invalid response."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code

