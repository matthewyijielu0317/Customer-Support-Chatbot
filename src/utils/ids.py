import hashlib
import re
from datetime import datetime, timezone


def cache_key_for_query(q: str) -> str:
    return hashlib.sha256(q.encode("utf-8")).hexdigest()


def generate_readable_session_id(user_id: str, timestamp: datetime = None) -> str:
    """Generate a human-readable session ID from email and timestamp.
    
    Format: {email_prefix}_{YY-MM-DD}_{HH:MM}
    Example: nbaudrey3c_25-09-23_10:05
    
    Args:
        user_id: User email address
        timestamp: Optional timestamp, defaults to current UTC time
        
    Returns:
        Human-readable session ID
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    # Extract email prefix (part before @)
    email_prefix = user_id.split('@')[0] if '@' in user_id else user_id
    
    # Clean the prefix to only include alphanumeric and basic chars
    email_prefix = re.sub(r'[^a-zA-Z0-9_-]', '', email_prefix)
    
    # Format timestamp as YY-MM-DD_HH:MM
    date_str = timestamp.strftime("%y-%m-%d")
    time_str = timestamp.strftime("%H:%M")
    
    return f"{email_prefix}_{date_str}_{time_str}"


