from functools import lru_cache
from pathlib import Path
import json

SCHEMA_FILE = Path(__file__).resolve().parent.parent / "schema.json"

@lru_cache()
def load_schema(path: Path | str = SCHEMA_FILE):
    """Load the JSON schema describing canonical fields and defaults."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def canonical_map(schema: dict | None = None) -> dict:
    """Return mapping of canonical field key to definition."""
    if schema is None:
        schema = load_schema()
    return {c["key"]: c for c in schema.get("canonical_fields", [])}
