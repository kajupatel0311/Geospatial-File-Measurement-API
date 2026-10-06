import threading
from typing import Optional

_store = {}
_lock = threading.Lock()

def save_file_record(file_id: str, data: dict):
    with _lock:
        _store[file_id] = data

def get_file_record(file_id: str) -> Optional[dict]:
    with _lock:
        return _store.get(file_id)
