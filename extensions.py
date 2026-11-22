from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def utcnow():
    """Return timezone-naive UTC datetime for consistent database compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

