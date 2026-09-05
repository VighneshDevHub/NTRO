from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WipeResult:
    method_name: str
    passes: int
    bytes_processed: int


class Wiper(ABC):
    method_name: str

    @abstractmethod
    def wipe(self, target: str, size_bytes: int) -> WipeResult:
        raise NotImplementedError
