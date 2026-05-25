from __future__ import annotations

from threading import Lock
from typing import Any, Dict, List

_store: Dict[str, List[Dict[str, Any]]] = {}
_lock = Lock()


def push(run_id: str, records: List[Dict[str, Any]]) -> None:
    with _lock:
        if run_id not in _store:
            _store[run_id] = []
        _store[run_id].extend(records)


def get(run_id: str, offset: int = 0) -> List[Dict[str, Any]]:
    with _lock:
        return list((_store.get(run_id) or [])[offset:])


def clear(run_id: str) -> None:
    with _lock:
        _store.pop(run_id, None)
