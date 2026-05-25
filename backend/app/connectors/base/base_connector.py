from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List


class BaseConnector(ABC):
    source_type: str

    @abstractmethod
    def extract(self, payload: bytes, filename: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_records: Iterable[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def validate(self, normalized_records: Iterable[Dict[str, Any]]) -> List[str]:
        raise NotImplementedError
