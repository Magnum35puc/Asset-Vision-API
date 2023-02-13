from typing import List
from models.Asset import Asset
from datetime import datetime, timedelta
import Configuration
from bson.objectid import ObjectId

from pymongo import MongoClient

client = MongoClient(Configuration.mongoDB_str)
db = client.AssetVision
assets_db = db.assets


class Portfolio():
    owner : str
    name: str
    assets: List[Asset]
    created_at: datetime = None
    last_updated_at: datetime = None


    def __init__(self, **kwargs):
        super().__init__()
        self.owner = kwargs.get('owner', None)
        self.name = kwargs.get('name', None)
        self.assets = kwargs.get('assets', [])
        self.created_at = kwargs.get('created_at', datetime.now())
        self.last_updated_at = kwargs.get('last_updated_at', datetime.now())

        if None in (self.owner, self.name):
            raise ValueError("Not all required attributes were provided")


    def serialize_asset(self):
        #Sol 1 DBREF
        asset_formatted = []
        for a in self.assets : 
            asset_id = ObjectId(assets_db.find_one({"symbol": a.symbol})['_id'])
            temp = {"$ref": "assets"}
            temp["$id"] = asset_id
            asset_formatted.append(temp)
        
        #Sol 2 Ref of ocject

        a = [s.symbol for s in self.assets]
        
        return {
            'name': self.name,
            'owner': self.owner,
            'assets': list(assets_db.find({"symbol":{"$in":a}})), #Or asset_formatted for the DBREF
            'created_at': self.created_at,
            'last_updated_at': self.last_updated_at
        }
  
""" 
asset_details = {"symbol": "ETH","name": "Ethereum","price": 1540,"currency": "USD","asset_class": "Cryptocurrency","industry": "Blockchain","marketplace": None,"user" : "TPUISE"}
asset = Asset(**asset_details)
p = Portfolio(owner = "12", name = "123", assets = [asset, asset])
print(p)
 """