from datetime import datetime

from pydantic import BaseModel
from typing import List

class User(BaseModel):
    username: str = None
    hashed_password: str = None
    email: str = None
    roles: List[str] = []
    created_at: datetime = None

    
    
    def __str__(self):
        return f"{self.username} ({self.roles})"
