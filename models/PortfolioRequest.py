from pydantic import BaseModel
from typing import List

class PortfolioRequest(BaseModel):
    assets_symbols: List[str] = []
    shares: List[float] = []
    cost_prices: List[float] = []
    portfolio_currency: str = "USD"
