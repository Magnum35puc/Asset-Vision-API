from pydantic import BaseModel
from typing import List

class PortfolioRequest(BaseModel):
    assets_symbols: List[str] = []
    shares: List[int] = []
    cost_prices: List[int] = []
    portfolio_currency: str = "USD"