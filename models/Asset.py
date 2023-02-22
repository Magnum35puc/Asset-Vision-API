from datetime import datetime, timedelta

from pydantic import BaseModel
import json 

class Asset(BaseModel):
    symbol: str = None
    name: str = None
    last_price: float = 0
    currency: str = None
    asset_class: str = None
    geo_zone: str = None
    industry: str = None
    created_by: str = None
    created_at: datetime = None
    last_updated_by: str = None
    last_updated_at: datetime = None
    
    
    def __str__(self):
        return f"{self.symbol} ({self.name})"
