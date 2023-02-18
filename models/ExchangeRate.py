from datetime import datetime, timedelta

from pydantic import BaseModel

class ExchangeRate(BaseModel):
    symbol: str = None
    base_currency: str
    target_currency: str
    last_rate: float = None
    created_by: str = None
    created_at: datetime = None
    last_updated_by: str = None
    last_updated_at: datetime = None
    
    
    def __str__(self):
        return f"{self.symbol} ({self.base_currency}-{self.target_currency})"
