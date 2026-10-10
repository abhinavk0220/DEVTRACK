import json
import os

from django.conf import settings


def load(filename):
    """Return the list of records in a JSON file ([] if missing or empty)."""
    path = settings.BASE_DIR / filename
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    return json.loads(content) if content else []


def save(filename, records):
    """Write records atomically: temp file first, then swap into place."""
    path = settings.BASE_DIR / filename
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    os.replace(tmp, path)


def next_id(records):
    """Next free integer ID: highest existing ID + 1, or 1 if empty."""
    return max((r['id'] for r in records), default=0) + 1