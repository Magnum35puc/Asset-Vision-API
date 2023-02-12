from pydantic import BaseModel

class Asset(BaseModel):
    symbol: str = None
    name: str = None
    shares: float = 0
    price: float = 0
    purchase_price: float = None
    currency: str = None
    asset_class: str = None
    industry: str = None
    yield_expected: float = 0
    marketplace : str = None
    
    def __init__(self, **kwargs):
        super().__init__()
        self.symbol = kwargs.get('symbol', None)
        self.name = kwargs.get('name', None)
        self.shares = kwargs.get('shares', 0)
        self.price = kwargs.get('price', 0)
        self.purchase_price = kwargs.get('purchase_price', None)
        self.currency = kwargs.get('currency', "EUR")
        self.asset_class = kwargs.get('asset_class', None)
        self.industry = kwargs.get('industry', None)
        self.yield_expected = kwargs.get('yield_expected', 0)
        self.marketplace = kwargs.get('marketplace', None)

        
        if None in (self.symbol, self.name):
            raise ValueError("Not all required attributes were provided")

        
    def __str__(self):
        return f"{self.symbol} ({self.name})"

    def cost(self):
        return self.shares*self.purchase_price

    def value(self): 
        return self.shares*self.price


""" details = {"symbol":"BTC", "name":"Bitcoin","shares" : 0.128318,"price":0,"purchase_price" : 23030,"currency" : "USD","asset_class" : "Cryptocurrency","industry" : "Blockchain"}
asset = Asset(**details)
print(asset) 
print(asset.shares) 
print(asset.purchase_price) 
print(asset.currency) 
print(asset.asset_class) 
print(asset)  """
