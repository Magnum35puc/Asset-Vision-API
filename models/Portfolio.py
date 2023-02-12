from typing import List
from models.Asset import Asset
from pydantic import BaseModel


class Portfolio(BaseModel):
    name: str
    assets: List[Asset]

