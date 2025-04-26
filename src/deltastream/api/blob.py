from dataclasses import dataclass
from typing import Optional, Union
import base64
import binascii


@dataclass
class Blob:
    """A class to handle binary data attachments for SQL queries.

    This class provides a simple way to handle binary data (BLOBs) that can be
    attached to SQL queries. It supports both raw bytes and base64 encoded data.
    """

    data: Union[bytes, str]
    name: Optional[str] = None
    content_type: Optional[str] = None
    encoding: str = "utf-8"

    def __post_init__(self):
        if isinstance(self.data, str):
            try:
                # First try to decode as base64
                self.data = base64.b64decode(self.data)
            except binascii.Error:
                # If not base64, treat as regular string
                if isinstance(self.data, str):  # Extra type check for mypy
                    self.data = self.data.encode(self.encoding)
        elif not isinstance(self.data, bytes):
            raise ValueError("data must be either str or bytes")

        # Ensure data is always bytes after initialization
        self.data = bytes(self.data)

    def to_bytes(self) -> bytes:
        assert isinstance(self.data, bytes)  # Will always be true after __post_init__
        return self.data

    def to_base64(self) -> str:
        data_bytes = self.to_bytes()
        return base64.b64encode(data_bytes).decode("ascii")

    @classmethod
    def from_bytes(
        cls, data: bytes, name: Optional[str] = None, content_type: Optional[str] = None
    ) -> "Blob":
        """Create a Blob from bytes data."""
        return cls(data=data, name=name, content_type=content_type)

    @classmethod
    def from_base64(
        cls, data: str, name: Optional[str] = None, content_type: Optional[str] = None
    ) -> "Blob":
        """Create a Blob from base64 encoded string."""
        return cls(data=data, name=name, content_type=content_type)


def to_bytes(data: Union[bytes, str]) -> bytes:
    if isinstance(data, str):
        return data.encode("utf-8")
    return data


def get_base64(data: Union[bytes, str]) -> str:
    binary_data = to_bytes(data)
    return base64.b64encode(binary_data).decode("utf-8")
