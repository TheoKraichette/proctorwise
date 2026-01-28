from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class User:
    user_id: str
    name: str
    email: str
    role: str
    hashed_password: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
