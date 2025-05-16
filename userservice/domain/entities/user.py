from dataclasses import dataclass

@dataclass
class User:
    user_id: str
    name: str
    email: str
    role: str
