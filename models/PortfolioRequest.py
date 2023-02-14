from pydantic import BaseModel
from typing import List

class PortfolioRequest(BaseModel):
    assets_symbols: List[str] = []
    shares: List[int] = []