from datetime import datetime, timedelta

from pydantic import BaseModel
import json 

class Asset(BaseModel):
    symbol: str = None
    name: str = None
    last_price: float = 0
    currency: str = None
    asset_class: str = None
    industry: str = None
    created_by: str = None
    created_at: datetime = None
    last_updated_by: str = None
    last_updated_at: datetime = None
    
    def __init__(self, **kwargs):
        super().__init__()
        self.symbol = kwargs.get('symbol', None)
        self.name = kwargs.get('name', None)
        self.last_price = kwargs.get('last_price', 0)
        self.currency = kwargs.get('currency', "EUR")
        self.asset_class = kwargs.get('asset_class', None)
        self.industry = kwargs.get('industry', None)
        self.created_by = kwargs.get('created_by', None)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.last_updated_by = kwargs.get('last_updated_by', None)
        self.last_updated_at = kwargs.get('last_updated_at', datetime.now())

        
        if None in (self.symbol, self.name):
            raise ValueError("Not all required attributes were provided")

        
    def __str__(self):
        return f"{self.symbol} ({self.name})"

    def serialize_asset(self):
        return {
            'symbol': self.symbol,
            'name': self.name,
            'last_price': self.last_price,
            'currency': self.currency,
            'asset_class': self.asset_class,
            'industry': self.industry,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'last_updated_by': self.last_updated_by,
            'last_updated_at': self.last_updated_at
        }
  

 
""" asset_details = {"symbol": "ETH","name": "Ethereum","price": 1540,"currency": "USD","asset_class": "Cryptocurrency","industry": "Blockchain","marketplace": None,"user" : "TPUISE"}
asset = Asset(**asset_details)

print(asset)
json_str = json.dumps(asset.__dict__)
print(json_str) """