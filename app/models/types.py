"""Custom SQLAlchemy types for SQLite compatibility."""
from sqlalchemy import TypeDecorator, Text
import json


class JSONEncodedType(TypeDecorator):
    """Custom type for JSON data that works with SQLite.
    
    Automatically serializes Python objects to JSON strings when storing,
    and deserializes JSON strings back to Python objects when retrieving.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert Python object to JSON string for storage."""
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        """Convert JSON string back to Python object."""
        if value is not None:
            return json.loads(value)
        return value
