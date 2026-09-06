from abc import abstractmethod
from typing import Protocol, runtime_checkable
@runtime_checkable
class FormattableLevel(Protocol):
    @abstractmethod
    def format_base(self) -> str:
        pass
    @abstractmethod
    def format_compact(self) -> str:
        pass
    @abstractmethod
    def format_full(self) -> str:
        pass