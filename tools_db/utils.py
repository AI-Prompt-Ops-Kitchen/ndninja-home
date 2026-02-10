import hashlib
from typing import Any, Dict
import json


def compute_hash(data: Any) -> str:
    """Compute SHA256 hash of data"""
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
    elif not isinstance(data, bytes):
        data = str(data)

    if isinstance(data, str):
        data = data.encode('utf-8')

    return hashlib.sha256(data).hexdigest()


def deep_compare(old: Any, new: Any) -> Dict[str, Any]:
    """Compare two objects and return differences"""
    changes = {}

    if isinstance(old, dict) and isinstance(new, dict):
        all_keys = set(old.keys()) | set(new.keys())
        for key in all_keys:
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val != new_val:
                changes[key] = {
                    "old": old_val,
                    "new": new_val
                }

    return changes
